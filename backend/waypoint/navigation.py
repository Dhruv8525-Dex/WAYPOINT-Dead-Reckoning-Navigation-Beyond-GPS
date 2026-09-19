"""Causal strapdown navigation with a 15-state error-state Kalman filter.

ENU navigation axes; quaternion rotates phone/body vectors into ENU. GPS is
passed only as available measurements; withheld reference is used after inference.
"""
import time
import numpy as np
from scipy.spatial.transform import Rotation

G = np.array([0., 0., 9.80665])
R_EARTH = 6378137.

def skew(v):
    x,y,z = v
    return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])

def local_coordinates(lat, lng, lat0, lng0):
    return np.column_stack(((np.asarray(lng)-lng0)*np.pi/180*R_EARTH*np.cos(np.deg2rad(lat0)), (np.asarray(lat)-lat0)*np.pi/180*R_EARTH))

def geodetic(xy, lat0, lng0):
    return np.column_stack((lat0+xy[:,1]/R_EARTH*180/np.pi, lng0+xy[:,0]/(R_EARTH*np.cos(np.deg2rad(lat0)))*180/np.pi))

def initial_rotation(gravity, heading_deg=0., mount_yaw_deg=0.):
    g = np.asarray(gravity, float)
    if np.linalg.norm(g) < 1: raise ValueError('Cannot initialize attitude without a gravity vector')
    tilt, _ = Rotation.align_vectors([G/np.linalg.norm(G)], [g/np.linalg.norm(g)])
    # Body +Y is the configured vehicle forward axis after mount yaw correction.
    forward = tilt.apply([0,1,0])
    current = np.arctan2(forward[0], forward[1])
    yaw = current - np.deg2rad(heading_deg + mount_yaw_deg)
    return Rotation.from_rotvec([0,0,yaw]) * tilt

class InertialFilter:
    def __init__(self, rotation, velocity, filtered=True, accel_noise=.3, gyro_noise=.02, gyro_bias=None, accel_bias=None):
        self.p = np.zeros(3); self.v = np.asarray(velocity, float).copy(); self.r = rotation
        self.ba = np.zeros(3) if accel_bias is None else np.array(accel_bias, float)
        self.bg = np.zeros(3) if gyro_bias is None else np.array(gyro_bias, float)
        self.P = np.diag([25.]*3+[4.]*3+[.05]*3+[.01]*3+[.001]*3)
        self.filtered=filtered; self.an=accel_noise; self.gn=gyro_noise

    def predict(self, acceleration, gyro, dt):
        if not 0 < dt <= 2: raise ValueError('Invalid integration interval')
        rot = self.r.as_matrix()
        a = np.asarray(acceleration)-self.ba; omega = np.asarray(gyro)-self.bg
        nav = rot @ a - G
        self.p += self.v*dt + .5*nav*dt*dt
        self.v += nav*dt
        self.r = self.r * Rotation.from_rotvec(omega*dt)
        if self.filtered:
            F=np.eye(15); F[0:3,3:6]=np.eye(3)*dt
            F[3:6,6:9]=-rot@skew(a)*dt; F[3:6,9:12]=-rot*dt
            F[6:9,6:9]-=skew(omega)*dt; F[6:9,12:15]=-np.eye(3)*dt
            Q=np.diag([1e-8]*3+[self.an**2]*3+[self.gn**2]*3+[1e-6]*3+[1e-8]*3)*dt
            self.P=F@self.P@F.T+Q

    def update(self, residual, H, noise):
        covariance=np.eye(len(residual))*noise**2
        S=H@self.P@H.T+covariance
        K=np.linalg.solve(S, H@self.P).T
        correction=K@residual
        self.p+=correction[:3]; self.v+=correction[3:6]
        self.r=self.r*Rotation.from_rotvec(correction[6:9])
        self.ba=np.clip(self.ba+correction[9:12],-2.,2.); self.bg=np.clip(self.bg+correction[12:15],-.1,.1)
        I=np.eye(15)-K@H
        self.P=I@self.P@I.T+K@covariance@K.T
        self.P=(self.P+self.P.T)*.5

    def planar(self):
        if self.filtered:
            H=np.zeros((2,15));H[0,2]=1;H[1,5]=1
            self.update(np.array([-self.p[2],-self.v[2]]),H,.5)

    def gps(self, xy, velocity, noise):
        if not self.filtered:
            self.p[:2]=xy;self.p[2]=0;self.v[2]=0
            if velocity is not None: self.v[:2]=velocity
            return
        H=np.zeros((2,15)); H[:,:2]=np.eye(2)
        self.update(np.asarray(xy)-self.p[:2],H,noise)
        if velocity is not None:
            H=np.zeros((2,15)); H[:,3:5]=np.eye(2)
            self.update(np.asarray(velocity)-self.v[:2],H,max(.5,noise*.15))

    def stationary(self):
        if self.filtered:
            H=np.zeros((3,15)); H[:,3:6]=np.eye(3)
            self.update(-self.v,H,.08)

    def learned_speed(self, speed, noise):
        # Velocity pseudo-observation along the current body forward direction.
        forward=self.r.apply([0,1,0]); forward[2]=0
        length=np.linalg.norm(forward)
        if length < .1: return
        forward/=length
        H=np.zeros((1,15)); H[0,3:6]=forward
        self.update(np.array([speed-np.dot(self.v,forward)]),H,noise)


def evaluate(df, config, predicted_speed=None, model_noise=3., calibration=None, progress=lambda p,m:None):
    started=time.perf_counter()
    t=df.t.to_numpy(); n=len(df)
    outages=np.zeros(n,dtype=bool)
    for outage in config.get('outages',[]): outages|=(t>=outage['start'])&(t<=outage['end'])
    valid=np.isfinite(df.lat)&np.isfinite(df.lng)
    available=valid.to_numpy() & ~outages
    if not available[0] and any(config.get(k) is None for k in ('initial_lat','initial_lng','initial_heading_deg','initial_speed_mps')):
        raise ValueError('First sample needs a usable GPS fix, or explicit initial position, heading and speed')
    lat0=float(df.lat.iloc[0]) if available[0] else config['initial_lat']
    lng0=float(df.lng.iloc[0]) if available[0] else config['initial_lng']
    ref=local_coordinates(df.lat,df.lng,lat0,lng0)
    # Never initialize from a withheld measurement.
    heading=config.get('initial_heading_deg')
    if heading is None:
        heading=float(df.heading.iloc[0]) if available[0] and np.isfinite(df.heading.iloc[0]) else None
    speed=config.get('initial_speed_mps')
    if speed is None: speed=float(df.speed.iloc[0]) if available[0] and np.isfinite(df.speed.iloc[0]) else None
    if heading is None or speed is None: raise ValueError('Provide initial heading and speed: the first fix does not contain both')
    gravity=df[['gravity_x','gravity_y','gravity_z']].iloc[0].to_numpy(float)
    if not np.isfinite(gravity).all():
        if calibration: gravity=np.array(calibration['gravity'])
        elif speed < .3: gravity=df[['ax','ay','az']].iloc[0].to_numpy(float)
        else: raise ValueError('Moving start without gravity data: select a stationary calibration profile')
    rotation=initial_rotation(gravity,heading,config.get('mount_yaw_deg',0))
    velocity=[speed*np.sin(np.deg2rad(heading)),speed*np.cos(np.deg2rad(heading)),0.]
    methods=['inertial','ekf'] + (['ml'] if predicted_speed is not None else [])
    filters={name:InertialFilter(rotation,velocity,name!='inertial',config.get('accel_noise',.3),config.get('gyro_noise',.02), (calibration or {}).get('gyro_bias'), (calibration or {}).get('accel_bias')) for name in methods}
    paths={k:np.zeros((n,2)) for k in methods}; velocities={k:np.zeros(n) for k in methods}
    uncertainty={k:np.zeros(n) for k in methods}; acc=df[['ax','ay','az']].to_numpy(); gyro=df[['gx','gy','gz']].to_numpy()
    gap_wait=False; skipped=0
    for i in range(n):
        if i%200==0: progress(int(i/n*95),f'Processing {i:,} / {n:,} samples')
        if i:
            dt=t[i]-t[i-1]
            if dt>2: gap_wait=True; skipped+=1
            if gap_wait and available[i]: gap_wait=False
            if not gap_wait and dt<=2:
                for f in filters.values(): f.predict(acc[i-1],gyro[i-1],dt)
        if available[i]:
            measured_velocity=None
            if np.isfinite(df.speed.iloc[i]) and np.isfinite(df.heading.iloc[i]):
                angle=np.deg2rad(df.heading.iloc[i]); measured_velocity=df.speed.iloc[i]*np.array([np.sin(angle),np.cos(angle)])
            for f in filters.values():
                f.gps(ref[i],measured_velocity,config.get('gps_noise',5))
                if measured_velocity is not None and np.linalg.norm(measured_velocity)>2:
                    forward=f.r.apply([0,1,0]); observed=np.arctan2(measured_velocity[0],measured_velocity[1]); estimated=np.arctan2(forward[0],forward[1]); difference=(estimated-observed+np.pi)%(2*np.pi)-np.pi
                    f.r=Rotation.from_rotvec([0,0,difference*.1])*f.r
        elif predicted_speed is not None and np.isfinite(predicted_speed[i]) and not gap_wait:
            filters['ml'].learned_speed(float(predicted_speed[i]), max(.5,model_noise))
        # A stationary update requires a sustained causal window, not instantaneous acceleration.
        start=max(0,i-9)
        stationary = i>=9 and np.max(np.linalg.norm(gyro[start:i+1],axis=1))<.025 and np.std(np.linalg.norm(acc[start:i+1],axis=1))<.025
        # Constant-velocity motion can resemble stillness; apply only with an available low-speed fix.
        if stationary and available[i] and np.isfinite(df.speed.iloc[i]) and df.speed.iloc[i]<.3:
            for f in filters.values(): f.stationary()
        for f in filters.values(): f.planar()
        for name,f in filters.items():
            paths[name][i]=f.p[:2]; velocities[name][i]=np.linalg.norm(f.v[:2]); uncertainty[name][i]=float(np.sqrt(max(0,np.trace(f.P[:2,:2]))))
            if not np.isfinite(f.p).all() or np.linalg.norm(f.p)>1e8: raise ValueError('Estimator diverged; inspect units, mounting and calibration')
    valid_mask=valid.to_numpy(); outage_mask=valid_mask&outages
    distances=np.linalg.norm(np.diff(ref,axis=0),axis=1); total=float(np.nansum(distances))
    metrics={}; series={};
    for name,xy in paths.items():
        error=np.linalg.norm(xy-ref,axis=1); error[~valid_mask]=np.nan
        mask=outage_mask if outage_mask.any() else valid_mask
        e=error[mask]; velmask=mask&np.isfinite(df.speed)
        metrics[name]={'position_rmse_m':float(np.sqrt(np.mean(e**2))) if len(e) else None,
            'endpoint_drift_m':float(e[-1]) if len(e) else None, 'max_error_m':float(np.max(e)) if len(e) else None,
            'normalized_drift_percent':float(e[-1]/total*100) if len(e) and total>0 else None,
            'velocity_rmse_mps':float(np.sqrt(np.mean((velocities[name][velmask]-df.speed.to_numpy()[velmask])**2))) if velmask.any() else None}
        gps=geodetic(xy,lat0,lng0)
        series[name]={'lat':gps[:,0].tolist(),'lng':gps[:,1].tolist(),'error':error.tolist(),'speed':velocities[name].tolist(),'uncertainty':uncertainty[name].tolist()}
    elapsed=time.perf_counter()-started
    return {'time':t.tolist(),'reference':{'lat':df.lat.tolist(),'lng':df.lng.tolist(),'speed':df.speed.tolist()},'outage':outages.tolist(),'series':series,'metrics':metrics,
            'duration_s':float(t[-1]),'distance_m':total,'runtime_s':elapsed,'samples_per_second':n/elapsed,'metric_scope':'outage samples' if outage_mask.any() else 'all reference samples',
            'gap_count':skipped,'engine_version':'1.0.1','notes':['GPS reference is withheld during configured outages.','Uncertainty is the filter covariance scale, not calibrated coverage.','GPS reference accuracy limits the measured errors.','Ground-vehicle planar constraints and bounded sensor-bias priors are applied. Available GPS course stabilizes yaw above 2 m/s.']}
