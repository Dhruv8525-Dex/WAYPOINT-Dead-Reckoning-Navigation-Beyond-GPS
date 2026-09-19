"""Reproducible, causal velocity learning. GPS is used only as a training label."""
import json
import time
import platform
import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from .config import DATA

CHANNELS=['ax','ay','az','gx','gy','gz']
WINDOW=50

def causal_samples(df):
    times=df.t.to_numpy(float); dt=float(np.median(np.diff(times)))
    raw=df[CHANNELS].to_numpy(float).copy()
    gravity=df[['gravity_x','gravity_y','gravity_z']].to_numpy(float)
    if np.isfinite(gravity).all(): raw[:,:3]-=gravity
    # Filter before downsampling; state resets at gaps and does not see future values.
    fs=1/dt; sos=butter(4,min(4.,fs*.4),fs=fs,output='sos')
    boundaries=np.r_[0,np.where(np.diff(times)>2)[0]+1,len(times)]
    for a,b in zip(boundaries[:-1],boundaries[1:]):
        for c in range(6): raw[a:b,c],_=sosfilt(sos,raw[a:b,c],zi=sosfilt_zi(sos)*raw[a,c])
    grid=np.arange(0,times[-1]+1e-8,.1)
    idx=np.searchsorted(times,grid,side='right')-1; idx=np.maximum(idx,0)
    samples=raw[idx]
    samples=np.column_stack((samples,np.linalg.norm(samples[:,:3],axis=1),np.linalg.norm(samples[:,3:6],axis=1)))
    valid=(grid-times[idx]<.25)
    speed=df.speed.to_numpy(float)[idx]
    valid&=np.isfinite(speed)
    valid&=(speed>=0)&(speed<=100)
    return grid,samples.astype(np.float32),speed.astype(np.float32),valid

def windows(df, stride=5):
    grid,x,y,valid=causal_samples(df)
    ends=np.arange(WINDOW-1,len(x),stride)
    ends=np.array([i for i in ends if valid[i-WINDOW+1:i+1].all()],dtype=int)
    if not len(ends): raise ValueError('No valid five-second windows with GPS speed labels')
    X=np.stack([x[i-WINDOW+1:i+1] for i in ends])
    return X,y[ends],grid[ends]

def features(x):
    return np.concatenate((x.mean(axis=1),x.std(axis=1),x[:,-1],np.percentile(x,90,axis=1)-np.percentile(x,10,axis=1)),axis=1)

def metrics(y,p):
    return {'mae_mps':float(mean_absolute_error(y,p)), 'rmse_mps':float(np.sqrt(mean_squared_error(y,p))), 'samples':len(y)}

def neural_class():
    import torch
    from torch import nn
    class VelocityNetwork(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv=nn.Conv1d(8,24,kernel_size=5)  # entire window is trailing; no lookahead
            self.gru=nn.GRU(24,32,batch_first=True)
            self.head=nn.Linear(32,1)
        def forward(self,x):
            x=torch.relu(self.conv(x.transpose(1,2))).transpose(1,2)
            x,_=self.gru(x)
            return self.head(x[:,-1]).squeeze(-1)
    return VelocityNetwork

def train(datasets, config, model_id, progress=lambda p,m:None):
    started=time.perf_counter(); seed=config.get('seed',42); np.random.seed(seed)
    groups={}
    for label in ('train','validation','test'):
        arrays=[windows(datasets[id]) for id in config[f'{label}_ids']]
        groups[label]=(np.concatenate([a[0] for a in arrays]),np.concatenate([a[1] for a in arrays]))
    x,y=groups['train']; architecture=config['architecture']; folder=DATA/'models'/model_id; folder.mkdir(parents=True,exist_ok=True)
    history=[]; backend='CPU'
    if architecture=='ridge':
        x=features(x); mean=x.mean(0); scale=x.std(0); scale[scale<1e-6]=1
        best=None
        for i,alpha in enumerate([.1,1.,10.,100.,1000.]):
            progress(10+i*12,f'Fitting ridge regularization {alpha:g}')
            model=Ridge(alpha=alpha).fit((x-mean)/scale,y)
            vx,vy=groups['validation']; prediction=np.maximum(0,model.predict((features(vx)-mean)/scale))
            score=metrics(vy,prediction)['rmse_mps']; history.append({'alpha':alpha,'validation_rmse_mps':score})
            if best is None or score<best[0]: best=(score,model,alpha)
        model=best[1]; np.savez(folder/'weights.npz',coef=model.coef_,intercept=model.intercept_,mean=mean,scale=scale)
        infer=lambda values: np.maximum(0,model.predict((features(values)-mean)/scale))
    else:
        import torch
        torch.set_num_threads(4); torch.manual_seed(seed)
        if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic=True; torch.backends.cudnn.benchmark=False
        device=torch.device('cuda' if torch.cuda.is_available() else 'cpu'); backend=str(device)
        mean=x.mean((0,1)); scale=x.std((0,1)); scale[scale<1e-6]=1
        model=neural_class()().to(device); optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.001)
        loss_fn=torch.nn.SmoothL1Loss(); target_mean=float(y.mean()); target_scale=max(float(y.std()),1.)
        def infer(values):
            model.eval(); values=(values-mean)/scale; output=[]
            with torch.no_grad():
                for start in range(0,len(values),256): output.extend((model(torch.tensor(values[start:start+256],device=device))*target_scale+target_mean).cpu().numpy())
            return np.maximum(0,np.array(output))
        best_score=float('inf'); stale=0
        for epoch in range(config.get('epochs',20)):
            progress(5+int(epoch/config.get('epochs',20)*80),f'Training epoch {epoch+1}')
            model.train(); order=np.random.permutation(len(x)); losses=[]
            for start in range(0,len(x),128):
                ids=order[start:start+128]; xb=torch.tensor((x[ids]-mean)/scale,device=device); yb=torch.tensor((y[ids]-target_mean)/target_scale,device=device)
                optimizer.zero_grad(); loss=loss_fn(model(xb),yb); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),1.);optimizer.step();losses.append(float(loss.item()))
            prediction=infer(groups['validation'][0]); score=metrics(groups['validation'][1],prediction)['rmse_mps']
            history.append({'epoch':epoch+1,'train_loss':float(np.mean(losses)),'validation_rmse_mps':score})
            if score<best_score-1e-4:
                best_score=score;stale=0;torch.save(model.state_dict(),folder/'weights.pt')
            else: stale+=1
            if stale>=5: break
        model.load_state_dict(torch.load(folder/'weights.pt',map_location=device,weights_only=True))
        np.savez(folder/'normalization.npz',mean=mean,scale=scale,target_mean=target_mean,target_scale=target_scale)
    progress(90,'Evaluating untouched test recording')
    test_x,test_y=groups['test']; start=time.perf_counter(); prediction=infer(test_x); latency=(time.perf_counter()-start)*1000/max(len(test_x),1)
    validation=metrics(groups['validation'][1],infer(groups['validation'][0]))
    report={'architecture':architecture,'seed':seed,'window_samples':WINDOW,'sample_rate_hz':10,'feature_version':1,'channels':CHANNELS+['accel_norm','gyro_norm'],
            'validation':validation,'test':metrics(test_y,prediction),'training_samples':len(y),'history':history,'config':config,
            'runtime_s':time.perf_counter()-started,'inference_ms_per_window':latency,'device':backend,'python':platform.python_version()}
    (folder/'manifest.json').write_text(json.dumps(report,indent=2))
    np.savez_compressed(folder/'test_predictions.npz',actual=test_y,predicted=prediction)
    return report

def predict(df, model_record):
    folder=DATA/'models'/model_record.id; manifest=json.loads((folder/'manifest.json').read_text())
    # No GPS labels required during inference. Validity is determined only by IMU timing.
    temporary=df.copy();temporary['speed']=0.
    grid,x,_,valid=causal_samples(temporary)
    ends=np.array([i for i in range(WINDOW-1,len(x)) if valid[i-WINDOW+1:i+1].all()],dtype=int)
    output=np.full(len(x),np.nan)
    if not len(ends): return np.full(len(df),np.nan)
    if manifest['architecture']=='ridge':
        weights=np.load(folder/'weights.npz',allow_pickle=False)
        for start in range(0,len(ends),256):
            batch=ends[start:start+256]; X=np.stack([x[i-WINDOW+1:i+1] for i in batch]);
            output[batch]=np.maximum(0,((features(X)-weights['mean'])/weights['scale'])@weights['coef']+weights['intercept'])
    else:
        import torch
        torch.set_num_threads(4); model=neural_class()(); model.load_state_dict(torch.load(folder/'weights.pt',map_location='cpu',weights_only=True)); model.eval()
        norm=np.load(folder/'normalization.npz',allow_pickle=False)
        with torch.no_grad():
            for start in range(0,len(ends),256):
                batch=ends[start:start+256]; X=np.stack([x[i-WINDOW+1:i+1] for i in batch]); values=model(torch.tensor((X-norm['mean'])/norm['scale'])).numpy()
                output[batch]=np.maximum(0,values*norm['target_scale']+norm['target_mean'])
    idx=np.minimum(np.maximum(np.searchsorted(grid,df.t,side='right')-1,0),len(grid)-1)
    return output[idx]
