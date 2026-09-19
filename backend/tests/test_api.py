import os
import tempfile
import json
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

# A separate workspace keeps test jobs, devices and destructive restore checks away from user data.
_test_dir=tempfile.TemporaryDirectory(prefix='waypoint-test-')
os.environ['WAYPOINT_DATA']=_test_dir.name
os.environ['WAYPOINT_NO_WORKER']='1'
from backend.waypoint.api import app
from backend.waypoint.db import Session,Job,Record,engine,read_engine
import atexit
atexit.register(engine.dispose)
atexit.register(read_engine.dispose)
from backend.waypoint.worker import execute

@pytest.fixture
def client():
    with TestClient(app) as client:yield client

def csv_bytes(n=200):
    return pd.DataFrame({'t':np.arange(n)*.1,'ax':0,'ay':0,'az':9.80665,'gx':0,'gy':0,'gz':0,'lat':12.,'lng':77.,'speed':0.,'heading':0.,'gravity_x':0.,'gravity_y':0.,'gravity_z':9.80665}).to_csv(index=False).encode()

def setup_recording(client):
    project=client.post('/api/v1/projects',json={'name':'Test project'}).json()
    upload=client.post('/api/v1/uploads',files={'file':('stationary.csv',csv_bytes(),'text/csv')})
    assert upload.status_code==201,upload.text
    body={'project_id':project['id'],'upload_id':upload.json()['upload_id'],'name':'Stationary','mapping':upload.json()['mapping']}
    imported=client.post('/api/v1/imports',json=body)
    assert imported.status_code==201,imported.text
    return project,imported.json(),body

def test_full_api_run_export_persistence(client):
    project,dataset,_=setup_recording(client)
    response=client.post('/api/v1/runs',json={'project_id':project['id'],'dataset_id':dataset['id'],'outages':[{'start':5,'end':15}]})
    assert response.status_code==202,response.text
    execute(response.json()['id'])
    job=client.get('/api/v1/jobs',params={'project_id':project['id']}).json()[0]
    assert job['status']=='completed',job
    result=client.get(f'/api/v1/runs/{job["result_id"]}/result').json()
    assert result['metrics']['ekf']['position_rmse_m']<1e-6
    for format in ('csv','json','html'):
        export=client.get(f'/api/v1/runs/{job["result_id"]}/export?format={format}')
        assert export.status_code==200 and len(export.content)>100
    with Session() as db:assert db.get(Record,job['result_id']).kind=='run'

def test_duplicate_upload_and_invalid_outage(client):
    project,dataset,body=setup_recording(client)
    assert client.post('/api/v1/imports',json=body).status_code==409
    assert client.post('/api/v1/runs',json={'project_id':project['id'],'dataset_id':dataset['id'],'outages':[{'start':10,'end':1000}]}).status_code==422
    assert client.post('/api/v1/uploads',files={'file':('bad.csv',b'a,b\n1,2','text/csv')}).status_code==422

def test_pairing_auth_dedup_and_revocation(client):
    code=client.post('/api/v1/pairing').json()['code']
    pair=client.post('/api/v1/device/pair',json={'code':code,'name':'Test phone'}).json()
    headers={'Authorization':'Bearer '+pair['token']}
    body={'session_id':'testsession','sequence':0,'samples':[{'t':0,'ax':0,'ay':0,'az':9.8,'gx':0,'gy':0,'gz':0}]}
    assert client.post('/api/v1/device/batches',json=body).status_code==401
    assert client.post('/api/v1/device/batches',json=body,headers=headers).json()['ack']==0
    assert client.post('/api/v1/device/batches',json=body,headers=headers).json()['duplicate'] is True
    body['samples'][0]['ax']=3
    assert client.post('/api/v1/device/batches',json=body,headers=headers).status_code==409
    client.post(f'/api/v1/devices/{pair["device_id"]}/revoke')
    assert client.post('/api/v1/device/batches',json=body,headers=headers).status_code==401

def test_origin_and_cross_project_boundaries(client):
    assert client.post('/api/v1/projects',json={'name':'x'},headers={'Origin':'https://evil.example'}).status_code==403
    project,dataset,_=setup_recording(client)
    other=client.post('/api/v1/projects',json={'name':'Other'}).json()
    assert client.post('/api/v1/runs',json={'project_id':other['id'],'dataset_id':dataset['id']}).status_code==404


def test_public_auth_cors_headers_and_read_only_database(client,monkeypatch):
    import base64
    from sqlalchemy import text
    from backend.waypoint import api as api_module
    from backend.waypoint.db import ReadSession
    monkeypatch.setattr(api_module,'PUBLIC',True)
    monkeypatch.setattr(api_module,'ADMIN_PASSWORD','a-safe-test-password-long-enough')
    monkeypatch.setattr(api_module,'ALLOWED_ORIGINS',frozenset({'https://waypoint.example'}))
    assert client.get('/api/v1/projects').status_code==401
    headers={'Authorization':'Basic '+base64.b64encode(b'waypoint:a-safe-test-password-long-enough').decode(), 'Origin':'https://waypoint.example'}
    result=client.get('/api/v1/projects',headers=headers)
    assert result.status_code==200
    assert result.headers['access-control-allow-origin']=='https://waypoint.example'
    assert result.headers['x-content-type-options']=='nosniff'
    assert result.headers['strict-transport-security'].startswith('max-age=')
    assert client.get('/api/v1/projects',headers={**headers,'Origin':'https://evil.example'}).status_code==403
    assert client.options('/api/v1/projects',headers={'Origin':'https://waypoint.example','Access-Control-Request-Method':'POST'}).status_code==204
    with ReadSession() as db:
        with pytest.raises(Exception):db.execute(text("INSERT INTO projects (id,name,description,created_at) VALUES ('forbidden','bad','','')"))


def test_api_rate_limit_and_invalid_name(client,monkeypatch):
    import time
    from backend.waypoint import api as api_module
    assert client.post('/api/v1/projects',json={'name':'  \u0000bad  '}).status_code==422
    monkeypatch.setattr(api_module,'PUBLIC',True)
    monkeypatch.setattr(api_module,'ADMIN_PASSWORD','a-safe-test-password-long-enough')
    import base64
    headers={'Authorization':'Basic '+base64.b64encode(b'waypoint:a-safe-test-password-long-enough').decode()}
    monkeypatch.setitem(api_module.REQUEST_RATE,('testclient','workspace'),[time.monotonic()]*180)
    result=client.get('/api/v1/projects',headers=headers)
    assert result.status_code==429 and result.headers['retry-after']=='60'

def test_cancel_and_calibration(client):
    project,dataset,_=setup_recording(client)
    calibration=client.post('/api/v1/calibrations',json={'project_id':project['id'],'dataset_id':dataset['id'],'start':0,'end':5})
    assert calibration.status_code==201,calibration.text
    job=client.post('/api/v1/runs',json={'project_id':project['id'],'dataset_id':dataset['id']}).json()
    assert client.post(f'/api/v1/jobs/{job["id"]}/cancel').json()['status']=='cancelled'

def test_backup_restore_and_zip_slip(client,tmp_path):
    from backend.waypoint.backup import backup,restore
    setup_recording(client)
    archive=backup(); restored=restore(archive,tmp_path/'restored')
    assert (restored/'waypoint.db').exists()
    with pytest.raises(ValueError,match='empty'):restore(archive,restored)
    import zipfile
    bad=tmp_path/'bad.zip'
    with zipfile.ZipFile(bad,'w') as z:z.writestr('backup-manifest.json','{"version":1,"sha256":{}}');z.writestr('../outside','x')
    with pytest.raises(ValueError,match='Unsafe'):restore(bad,tmp_path/'safe')
