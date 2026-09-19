import asyncio
import hashlib
import hmac
import html
import io
import json
import logging
import multiprocessing as mp
import os
import secrets
import shutil
import time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, File, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, delete
from .config import DATA, ROOT, MAX_UPLOAD, VERSION, PUBLIC, ADMIN_PASSWORD, ALLOWED_ORIGINS
from .db import Session, ReadSession, Project, Record, Job, Device, Batch, now, uid, migrate, record_dict
from .schemas import *
from .ingest import preview, normalize, save_normalized, checksum, load_dataset, REQUIRED
from .worker import clean, run_worker
from .tls import ensure_certificate

PAIR_CODES={}
RATE={}
REQUEST_RATE={}

@asynccontextmanager
async def lifespan(app):
    migrate()
    stop=mp.Event();process=None
    if os.environ.get('WAYPOINT_NO_WORKER')!='1':
        process=mp.Process(target=run_worker,args=(stop,),daemon=True);process.start()
    yield
    stop.set()
    if process:
        process.join(timeout=3)
        if process.is_alive(): process.terminate();process.join(timeout=3)

app=FastAPI(title='Waypoint local research API',version=VERSION,lifespan=lifespan)

@app.middleware('http')
async def local_boundary(request,call_next):
    host=request.client.host if request.client else ''
    local=host in ('127.0.0.1','::1','localhost','testclient')
    route=request.url.path
    if not PUBLIC and not local and not route.startswith('/api/v1/device/'):
        return JSONResponse({'detail':'Workspace access is local only. Use paired-device endpoints.'},403)
    origin=request.headers.get('origin')
    if origin and origin.rstrip('/') not in ALLOWED_ORIGINS:
        return JSONResponse({'detail':'Origin is not allowed'},403)
    hostname=request.url.hostname
    if not PUBLIC and local and hostname not in ('127.0.0.1','localhost','::1','testserver'):
        return JSONResponse({'detail':'Host is not allowed'},400)
    if PUBLIC and request.method != 'OPTIONS' and route.startswith('/api/') and route != '/api/v1/health' and not route.startswith('/api/v1/device/'):
        from base64 import b64decode
        authorization=request.headers.get('authorization','')
        try:
            scheme, encoded = authorization.split(' ',1)
            username, password = b64decode(encoded,validate=True).decode().split(':',1)
            authorized = scheme.lower() == 'basic' and username == 'waypoint' and hmac.compare_digest(password,ADMIN_PASSWORD)
        except (ValueError,UnicodeError):
            authorized = False
        if not authorized:
            return JSONResponse({'detail':'Workspace authentication required'},401,headers={'WWW-Authenticate':'Basic realm="Waypoint"'})
    if route.startswith('/api/') and request.method != 'OPTIONS':
        key=(host, 'device' if route.startswith('/api/v1/device/') else 'workspace')
        current=time.monotonic()
        hits=REQUEST_RATE.setdefault(key,[])
        hits[:]=[t for t in hits if current-t<60]
        limit=240 if key[1]=='device' else 600 if local and not PUBLIC else 180
        if len(hits)>=limit:
            return JSONResponse({'detail':'Too many requests'},429,headers={'Retry-After':'60'})
        hits.append(current)
    length=request.headers.get('content-length')
    if length and (not length.isdigit() or int(length)>MAX_UPLOAD+1024*1024): return JSONResponse({'detail':'Upload exceeds 128 MB'},413)
    if request.method == 'OPTIONS' and origin:
        response=JSONResponse({},204)
        response.headers['Access-Control-Allow-Methods']='GET, POST, PATCH, OPTIONS'
        response.headers['Access-Control-Allow-Headers']='Authorization, Content-Type'
        response.headers['Access-Control-Max-Age']='600'
    else:
        response=await call_next(request)
    if origin and origin.rstrip('/') in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin']=origin
        response.headers['Vary']='Origin'
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://*.tile.openstreetmap.org; font-src 'self' data:; connect-src 'self' https: wss:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    if PUBLIC: response.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
    response.headers['Cache-Control']='no-store' if route.startswith('/api') else 'no-cache'
    return response

@app.exception_handler(ValueError)
async def value_error(_,exc): return JSONResponse({'detail':str(exc)},422)

@app.get('/api/v1/health')
def health():
    return {'status':'ok','version':VERSION,'data_dir':str(DATA),'mode':'single-user local','gpu_training':'optional'}

@app.get('/api/v1/projects',response_model=list[ProjectOut])
def projects():
    with ReadSession() as db:return [record_dict(p) for p in db.scalars(select(Project).order_by(Project.created_at.desc()))]

@app.post('/api/v1/projects',response_model=ProjectOut,status_code=201)
def create_project(body:ProjectInput):
    with Session() as db:
        p=Project(**body.model_dump());db.add(p);db.commit();return record_dict(p)

@app.patch('/api/v1/projects/{id}',response_model=ProjectOut)
def update_project(id:str,body:ProjectInput):
    with Session() as db:
        p=db.get(Project,id)
        if not p:raise HTTPException(404,'Project not found')
        p.name=body.name;p.description=body.description;db.commit();return record_dict(p)

def require_project(db,id):
    if not db.get(Project,id):raise HTTPException(404,'Project not found')

def require_record(db,id,kind=None,project=None):
    record=db.get(Record,id)
    if not record or (kind and record.kind!=kind) or (project and record.project_id!=project):raise HTTPException(404,'Record not found in this project')
    return record

@app.get('/api/v1/records',response_model=list[RecordOut])
def records(project_id:str,kind:Literal['dataset','run','model','calibration']|None=None):
    with ReadSession() as db:
        query=select(Record).where(Record.project_id==project_id)
        if kind:query=query.where(Record.kind==kind)
        return [record_dict(r) for r in db.scalars(query.order_by(Record.created_at.desc()))]

@app.get('/api/v1/records/{id}',response_model=RecordOut)
def get_record(id:str):
    with ReadSession() as db:return record_dict(require_record(db,id))

@app.post('/api/v1/uploads',status_code=201)
async def upload(file:UploadFile=File(...)):
    suffix=Path(file.filename or '').suffix.lower()
    if suffix not in ('.csv','.json','.txt'):raise HTTPException(422,'Choose CSV or versioned JSON')
    id=uid();target=DATA/'uploads'/f'{id}{suffix}';size=0
    try:
        with target.open('wb') as output:
            while block:=await file.read(1024*1024):
                size+=len(block)
                if size>MAX_UPLOAD:raise HTTPException(413,'Upload exceeds 128 MB')
                output.write(block)
        details=await asyncio.to_thread(preview,target)
        with Session() as db:
            db.add(Record(id=id,kind='upload',name=Path(file.filename).name,data={'path':str(target.relative_to(DATA))}));db.commit()
        return {'upload_id':id,**clean(details)}
    except Exception:
        target.unlink(missing_ok=True);raise

@app.post('/api/v1/imports',response_model=RecordOut,status_code=201)
def import_data(body:ImportInput):
    with Session() as db:
        require_project(db,body.project_id);upload=require_record(db,body.upload_id,'upload');path=DATA/upload.data['path']
        df,report=normalize(path,body.mapping,body.time_unit,body.gyro_unit,body.segment)
        digest=checksum(path)
        existing=[r for r in db.scalars(select(Record).where(Record.kind=='dataset',Record.project_id==body.project_id)) if r.data['checksum']==digest]
        if existing:raise HTTPException(409,'This exact recording already exists in the project')
        id=uid();raw=DATA/'raw'/f'{id}{path.suffix}';shutil.copyfile(path,raw)
        processed=save_normalized(df,id)
        record=Record(id=id,kind='dataset',project_id=body.project_id,name=body.name,data={**report,'checksum':digest,'raw_path':str(raw.relative_to(DATA)),'processed_path':processed,'source':body.source,'mapping':body.mapping,'time_unit':body.time_unit,'gyro_unit':body.gyro_unit})
        db.add(record);db.commit();return record_dict(record)

@app.get('/api/v1/datasets/{id}/samples')
def samples(id:str,limit:int=1500):
    with Session() as db:df=load_dataset(require_record(db,id,'dataset'))
    step=max(1,int(np.ceil(len(df)/max(10,min(limit,5000)))))
    return clean(df.iloc[::step].to_dict('records'))

@app.post('/api/v1/calibrations',response_model=RecordOut,status_code=201)
def calibrate(body:CalibrationInput):
    with Session() as db:
        require_project(db,body.project_id);r=require_record(db,body.dataset_id,'dataset',body.project_id);df=load_dataset(r)
        segment=df[(df.t>=body.start)&(df.t<=body.end)]
        if body.end-body.start<3 or len(segment)<20:raise ValueError('Choose at least three stationary seconds and 20 samples')
        accel=segment[['ax','ay','az']].to_numpy();gyro=segment[['gx','gy','gz']].to_numpy()
        if np.std(np.linalg.norm(accel,axis=1))>.15 or np.max(np.linalg.norm(gyro,axis=1))>.1:raise ValueError('Segment is not stationary enough for calibration')
        valid_speed=segment.speed.dropna()
        if len(valid_speed) and valid_speed.max()>.5:raise ValueError('GPS reports motion during calibration')
        gravity=accel.mean(0);bias=gravity-gravity/np.linalg.norm(gravity)*9.80665
        data={'gravity':gravity.tolist(),'accel_bias':bias.tolist(),'gyro_bias':gyro.mean(0).tolist(),'dataset_id':r.id,'interval':[body.start,body.end],'mounting':'Rigid mount; phone +Y configured forward'}
        record=Record(kind='calibration',project_id=body.project_id,name=body.name,data=data);db.add(record);db.commit();return record_dict(record)

@app.post('/api/v1/runs',response_model=JobOut,status_code=202)
def run(body:RunInput):
    with Session() as db:
        require_project(db,body.project_id);dataset=require_record(db,body.dataset_id,'dataset',body.project_id)
        for outage in body.outages:
            if outage.end>dataset.data['duration_s']:raise ValueError('Outage extends beyond the recording')
        if body.model_id:require_record(db,body.model_id,'model',body.project_id)
        if body.calibration_id:require_record(db,body.calibration_id,'calibration',body.project_id)
        job=Job(project_id=body.project_id,kind='run',config=body.model_dump());db.add(job);db.commit();return record_dict(job)

@app.post('/api/v1/training',response_model=JobOut,status_code=202)
def training(body:TrainInput):
    with Session() as db:
        require_project(db,body.project_id);all_ids=body.train_ids+body.validation_ids+body.test_ids
        recordings=[require_record(db,i,'dataset',body.project_id) for i in all_ids]
        if len({r.data['checksum'] for r in recordings})!=len(recordings):raise ValueError('Dataset content overlaps between splits')
        job=Job(project_id=body.project_id,kind='training',config=body.model_dump());db.add(job);db.commit();return record_dict(job)

@app.get('/api/v1/jobs',response_model=list[JobOut])
def jobs(project_id:str):
    with ReadSession() as db:return [record_dict(j) for j in db.scalars(select(Job).where(Job.project_id==project_id).order_by(Job.created_at.desc()))]

@app.post('/api/v1/jobs/{id}/cancel',response_model=JobOut)
def cancel(id:str):
    with Session() as db:
        job=db.get(Job,id)
        if not job:raise HTTPException(404,'Job not found')
        if job.status=='queued':job.status='cancelled'
        elif job.status=='running':job.status='cancel_requested'
        else:raise HTTPException(409,'Job is not active')
        job.updated_at=now();db.commit();return record_dict(job)

@app.get('/api/v1/events')
async def events(request:Request,project_id:str):
    async def stream():
        previous=''
        while not await request.is_disconnected():
            current=json.dumps(jobs(project_id))
            if current!=previous:yield f'data: {current}\n\n';previous=current
            else:yield ': heartbeat\n\n'
            await asyncio.sleep(1)
    return StreamingResponse(stream(),media_type='text/event-stream')

@app.get('/api/v1/runs/{id}/result')
def result(id:str):
    with Session() as db:r=require_record(db,id,'run')
    return FileResponse(DATA/r.data['path'],media_type='application/json')

@app.get('/api/v1/runs/{id}/export')
def export(id:str,format:Literal['json','csv','html']='json'):
    with Session() as db:r=require_record(db,id,'run')
    result=json.loads((DATA/r.data['path']).read_text())
    if format=='json':return FileResponse(DATA/r.data['path'],filename=f'waypoint-{id}.json',media_type='application/json')
    if format=='csv':
        import csv
        output=io.StringIO();writer=csv.writer(output);methods=list(result['series'])
        writer.writerow(['time_s','reference_lat','reference_lng','outage']+[f'{m}_{v}' for m in methods for v in ('lat','lng','error','speed')])
        for i,t in enumerate(result['time']):writer.writerow([t,result['reference']['lat'][i],result['reference']['lng'][i],result['outage'][i]]+[result['series'][m][v][i] for m in methods for v in ('lat','lng','error','speed')])
        return StreamingResponse(iter([output.getvalue()]),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="waypoint-{id}.csv"'})
    rows=''.join(f'<tr><th>{html.escape(method)}</th><td>{m["position_rmse_m"]}</td><td>{m["endpoint_drift_m"]}</td><td>{m["velocity_rmse_mps"]}</td></tr>' for method,m in result['metrics'].items())
    return HTMLResponse(f'<!doctype html><meta charset="utf-8"><title>Waypoint report</title><style>body{{font-family:system-ui;max-width:900px;margin:50px auto;padding:20px;color:#294333}}td,th{{padding:15px;border-bottom:1px solid #ddd;text-align:left}}pre{{white-space:pre-wrap}}@media print{{button{{display:none}}}}</style><h1>{html.escape(r.name)}</h1><p>Waypoint · real-data navigation experiment</p><p>Metric scope: {result["metric_scope"]}</p><table><tr><th>Method</th><th>Position RMSE (m)</th><th>Endpoint drift (m)</th><th>Velocity RMSE (m/s)</th></tr>{rows}</table><h2>Reproducibility</h2><pre>{html.escape(json.dumps(result["config"],indent=2))}</pre><p>Source SHA256: {result["dataset_checksum"]}</p><p>GPS accuracy limits these measurements. This report is not a certification of navigation performance.</p><button onclick="print()">Print / save PDF</button>')

@app.get('/api/v1/backup')
def backup_download():
    with Session() as db:
        if db.scalars(select(Job).where(Job.status.in_(['running','queued','cancel_requested']))).first():raise HTTPException(409,'Wait for jobs to finish before backing up')
    from .backup import backup
    return FileResponse(backup(),filename='waypoint-backup.zip')

@app.get('/api/v1/devices')
def devices():
    with ReadSession() as db:return [record_dict(d) for d in db.scalars(select(Device))]

@app.post('/api/v1/pairing')
def pairing():
    code=secrets.token_hex(4).upper();PAIR_CODES[code]=time.time()+300
    _,_,fingerprint=ensure_certificate()
    return {'code':code,'expires_in':300,'certificate_sha256':fingerprint,'port':8443}

@app.post('/api/v1/devices/{id}/revoke')
def revoke(id:str):
    with Session() as db:
        d=db.get(Device,id)
        if not d:raise HTTPException(404,'Device not found')
        d.revoked=1;db.commit();return {'revoked':True}

@app.post('/api/v1/device/pair')
def pair(body:PairInput,request:Request):
    host=request.client.host; attempts=RATE.setdefault(host,[]);attempts[:]=[t for t in attempts if time.time()-t<60]
    if len(attempts)>=5:raise HTTPException(429,'Wait one minute before trying again')
    attempts.append(time.time())
    if PAIR_CODES.pop(body.code.upper(),0)<time.time():raise HTTPException(401,'Invalid or expired pairing code')
    token=secrets.token_urlsafe(32)
    with Session() as db:
        d=Device(name=body.name,token_hash=hashlib.sha256(token.encode()).hexdigest());db.add(d);db.commit();return {'device_id':d.id,'token':token}

def authorize_device(token):
    hashed=hashlib.sha256(token.encode()).hexdigest()
    with Session() as db:
        device=db.scalars(select(Device).where(Device.token_hash==hashed,Device.revoked==0)).first()
        if not device:raise HTTPException(401,'Pair this device or renew its revoked credentials')
        return device.id

def accept_batch(device_id,body):
    for sample in body.samples:
        if any(k not in sample or sample[k] is None or not np.isfinite(sample[k]) for k in REQUIRED):raise ValueError('Every sample requires finite t, ax, ay, az, gx, gy, gz')
    times=[s['t'] for s in body.samples]
    if any(b<=a for a,b in zip(times,times[1:])):raise ValueError('Batch timestamps must increase')
    digest=hashlib.sha256(json.dumps(body.model_dump(),sort_keys=True).encode()).hexdigest()
    with Session() as db:
        existing=db.scalars(select(Batch).where(Batch.device_id==device_id,Batch.session_id==body.session_id,Batch.sequence==body.sequence)).first()
        if existing:
            if existing.checksum!=digest:raise HTTPException(409,'Sequence already acknowledged with different content')
            return {'ack':body.sequence,'duplicate':True}
        previous=db.scalars(select(Batch).where(Batch.device_id==device_id,Batch.session_id==body.session_id).order_by(Batch.sequence.desc()).limit(1)).first()
        expected=previous.sequence+1 if previous else 0
        if body.sequence!=expected:raise HTTPException(409,f'Expected sequence {expected}')
        if previous and times[0]<=previous.payload['samples'][-1]['t']:raise ValueError('Timestamps overlap the previous batch')
        db.add(Batch(device_id=device_id,session_id=body.session_id,sequence=body.sequence,checksum=digest,payload=body.model_dump()));db.commit()
    return {'ack':body.sequence,'duplicate':False}

@app.post('/api/v1/device/batches')
def device_batch(body:BatchInput,request:Request):
    token=request.headers.get('authorization','').removeprefix('Bearer ')
    return accept_batch(authorize_device(token),body)

@app.websocket('/api/v1/device/stream')
async def device_stream(ws:WebSocket):
    await ws.accept()
    try:
        auth=await asyncio.wait_for(ws.receive_json(),timeout=10);device_id=authorize_device(auth.get('token',''))
        await ws.send_json({'ready':True})
        while True:
            body=BatchInput.model_validate(await ws.receive_json())
            authorize_device(auth.get('token',''))
            await ws.send_json(await asyncio.to_thread(accept_batch,device_id,body))
    except WebSocketDisconnect:pass
    except Exception:
        await ws.close(code=1008)

@app.get('/api/v1/recordings')
def recordings():
    with ReadSession() as db:
        batches=list(db.scalars(select(Batch).order_by(Batch.created_at)))
    grouped={}
    for batch in batches:
        key=f'{batch.device_id}:{batch.session_id}'
        row=grouped.setdefault(key,{'device_id':batch.device_id,'session_id':batch.session_id,'batches':0,'samples':0,'last_sample':{},'updated_at':batch.created_at})
        row['batches']+=1;row['samples']+=len(batch.payload['samples']);row['last_sample']=batch.payload['samples'][-1];row['updated_at']=batch.created_at
    return list(grouped.values())

@app.post('/api/v1/recordings/{device_id}/{session_id}/import',response_model=RecordOut)
def import_recording(device_id:str,session_id:str,body:ProjectInput,project_id:str):
    with Session() as db:
        require_project(db,project_id);batches=list(db.scalars(select(Batch).where(Batch.device_id==device_id,Batch.session_id==session_id).order_by(Batch.sequence)))
        if not batches:raise HTTPException(404,'No received recording')
        samples=[s for b in batches for s in b.payload['samples']];id=uid();path=DATA/'uploads'/f'{id}.json'
        path.write_text(json.dumps({'version':1,'samples':samples}))
        db.add(Record(id=id,kind='upload',name=body.name,data={'path':str(path.relative_to(DATA))}));db.commit()
    return import_data(ImportInput(upload_id=id,project_id=project_id,name=body.name,source=f'Android device {device_id}; session {session_id}'))

@app.get('/api/v1/android/apk')
def apk():
    path=ROOT/'artifacts'/'waypoint-recorder.apk'
    if not path.exists():raise HTTPException(404,'Android APK has not been built yet')
    return FileResponse(path,filename='waypoint-recorder.apk',media_type='application/vnd.android.package-archive')

# Serve the built website without making API mistakes fall through to HTML.
if (ROOT/'dist'/'assets').exists():app.mount('/assets',StaticFiles(directory=ROOT/'dist'/'assets'),name='assets')
@app.get('/{route:path}',include_in_schema=False)
def website(route:str):
    if route.startswith('api/'):raise HTTPException(404,'API endpoint not found')
    path=ROOT/'dist'/'index.html'
    if path.exists():return FileResponse(path)
    return HTMLResponse('Build the website with npm run build, or run the frontend development server.',503)
