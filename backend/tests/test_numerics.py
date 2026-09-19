import numpy as np
import pandas as pd
import pytest
from scipy.spatial.transform import Rotation
from backend.waypoint.navigation import InertialFilter,initial_rotation,local_coordinates,geodetic,evaluate
from backend.waypoint.ingest import normalize
from backend.waypoint.ml import windows
from backend.waypoint.schemas import TrainInput

def recording(n=200):
    t=np.arange(n)*.1
    return pd.DataFrame({'t':t,'ax':0.,'ay':0.,'az':9.80665,'gx':0.,'gy':0.,'gz':0.,'lat':12.,'lng':77.,'speed':0.,'heading':0.,'accuracy':3.,'gravity_x':0.,'gravity_y':0.,'gravity_z':9.80665})

def test_stationary_and_acceleration():
    f=InertialFilter(Rotation.identity(),[0,0,0],False)
    for _ in range(100):f.predict([0,0,9.80665],[0,0,0],.1)
    assert np.linalg.norm(f.p)<1e-9
    for _ in range(100):f.predict([1,0,9.80665],[0,0,0],.1)
    assert f.p[0]==pytest.approx(50,abs=1e-7)

def test_rotations_and_roundtrip():
    r=initial_rotation([0,9.80665,0],90)
    assert np.linalg.norm(r.apply([0,9.80665,0])-[0,0,9.80665])<1e-7
    p=np.array([[50,20],[-10,60]])
    gps=geodetic(p,12,77)
    assert np.allclose(local_coordinates(gps[:,0],gps[:,1],12,77),p)

def test_withheld_gps_does_not_change_predictions():
    a=recording();b=a.copy(); b.loc[50:150,'lat']=40.;b.loc[50:150,'speed']=70.
    config={'outages':[{'start':5,'end':15}]}
    first=evaluate(a,config);second=evaluate(b,config)
    for method in ('inertial','ekf'):
        assert np.allclose(first['series'][method]['lat'][:151],second['series'][method]['lat'][:151])

def test_invalid_time_and_missing_columns(tmp_path):
    p=tmp_path/'bad.csv';recording().drop(columns='gz').to_csv(p,index=False)
    with pytest.raises(ValueError,match='Map required'):normalize(p)
    df=recording();df.loc[1,'t']=0;df.to_csv(p,index=False)
    with pytest.raises(ValueError,match='strictly'):normalize(p)

def test_causal_windows():
    a=recording();b=a.copy();b.loc[150:,'ax']=100
    x,_,_=windows(a,1);y,_,_=windows(b,1)
    assert np.allclose(x[:100],y[:100])

def test_split_rejects_overlap():
    with pytest.raises(ValueError,match='disjoint'):TrainInput(project_id='p',train_ids=['a'],validation_ids=['a'],test_ids=['b'])

def test_no_reference_metrics():
    df=recording();df[['lat','lng','speed','heading']]=np.nan
    result=evaluate(df,{'initial_lat':12,'initial_lng':77,'initial_heading_deg':0,'initial_speed_mps':0})
    assert result['metrics']['ekf']['position_rmse_m'] is None
