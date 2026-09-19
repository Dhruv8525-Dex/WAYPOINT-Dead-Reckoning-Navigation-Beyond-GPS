"""Durable single-worker queue, isolated from HTTP and UI threads."""
import json
import math
import time
import traceback
import sys
import logging
from sqlalchemy import select, update
from .db import Session, Job, Record, now, uid, migrate
from .config import DATA
from .ingest import load_dataset

class Cancelled(Exception): pass

def clean(value):
    if isinstance(value,float) and not math.isfinite(value): return None
    if isinstance(value,dict): return {k:clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [clean(v) for v in value]
    return value

def execute(job_id):
    with Session() as db:
        job=db.get(Job,job_id); config=job.config; kind=job.kind; project=job.project_id
    def progress(percent,message):
        with Session() as db:
            job=db.get(Job,job_id)
            if job.status=='cancel_requested': raise Cancelled()
            job.progress=percent;job.message=message;job.updated_at=now();db.commit()
    try:
        result_id=uid()
        if kind=='run':
            from .navigation import evaluate
            from .ml import predict
            with Session() as db:
                dataset=db.get(Record,config['dataset_id']); df=load_dataset(dataset)
                model=db.get(Record,config['model_id']) if config.get('model_id') else None
                calibration=db.get(Record,config['calibration_id']) if config.get('calibration_id') else None
            progress(1,'Loading causal estimator')
            speeds=predict(df,model) if model else None
            result=evaluate(df,config,speeds,model.data['validation']['rmse_mps'] if model else 3.,calibration.data if calibration else None,progress)
            result['config']=config;result['dataset_checksum']=dataset.data['checksum']
            if model: result['model_id']=model.id
            path=DATA/'results'/f'{result_id}.json';path.write_text(json.dumps(clean(result),allow_nan=False))
            data={k:v for k,v in result.items() if k not in ('time','reference','outage','series')}
            data['path']=str(path.relative_to(DATA));data['dataset_name']=dataset.name;record_kind='run'
        else:
            from .ml import train
            with Session() as db:
                records={i:db.get(Record,i) for label in ('train','validation','test') for i in config[f'{label}_ids']}
                datasets={i:load_dataset(r) for i,r in records.items()}
            data=train(datasets,config,result_id,progress)
            data['checksums']={i:r.data['checksum'] for i,r in records.items()};record_kind='model'
            (DATA/'models'/result_id/'manifest.json').write_text(json.dumps(data,indent=2))
        progress(99,'Saving immutable result')
        with Session() as db:
            job=db.get(Job,job_id)
            if job.status=='cancel_requested': raise Cancelled()
            db.add(Record(id=result_id,kind=record_kind,project_id=project,name=config['name'],data=clean(data)))
            job.status='completed';job.progress=100;job.message='Completed';job.result_id=result_id;job.updated_at=now();db.commit()
    except Cancelled:
        with Session() as db:
            job=db.get(Job,job_id);job.status='cancelled';job.message='Cancelled; no result published';job.updated_at=now();db.commit()
    except Exception as exc:
        logging.exception('Job %s failed',job_id)
        with Session() as db:
            job=db.get(Job,job_id);job.status='failed';job.message=str(exc) if isinstance(exc,ValueError) else 'Processing failed. See local worker log.';job.updated_at=now();db.commit()

def run_worker(stop):
    migrate()
    with Session() as db:
        db.execute(update(Job).where(Job.status.in_(['running','cancel_requested'])).values(status='interrupted',message='Application stopped before completion. Retry as a new job.',updated_at=now()));db.commit()
    while not stop.is_set():
        with Session() as db:
            job=db.scalars(select(Job).where(Job.status=='queued').order_by(Job.created_at).limit(1)).first()
            if job:
                job.status='running';job.updated_at=now();job.message='Starting';db.commit();id=job.id
            else: id=None
        if id: execute(id)
        else: stop.wait(.5)
