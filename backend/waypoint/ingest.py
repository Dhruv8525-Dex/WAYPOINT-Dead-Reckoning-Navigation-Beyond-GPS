"""Validated recording adapters. Raw data is never modified."""
import hashlib
import io
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .config import DATA

REQUIRED = ['t', 'ax', 'ay', 'az', 'gx', 'gy', 'gz']
OPTIONAL = ['lat', 'lng', 'speed', 'heading', 'accuracy', 'gravity_x', 'gravity_y', 'gravity_z']
PREFIXES = {
    't': 'TIME SINCE START', 'ax': 'ACCELEROMETER X', 'ay': 'ACCELEROMETER Y', 'az': 'ACCELEROMETER Z',
    'gx': 'GYROSCOPE Pitch', 'gy': 'GYROSCOPE Roll', 'gz': 'GYROSCOPE Yaw',
    'lat': 'GPS LATITUDE', 'lng': 'GPS LONGITUDE', 'speed': 'GPS SPEED',
    'heading': 'GPS ORIENTATION', 'accuracy': 'GPS ACCURACY',
    'gravity_x': 'GRAVITY X', 'gravity_y': 'GRAVITY Y', 'gravity_z': 'GRAVITY Z',
}

def read_table(path: Path):
    raw = path.read_bytes()
    if path.suffix.lower() == '.json':
        payload = json.loads(raw)
        if isinstance(payload, dict):
            if payload.get('version') != 1: raise ValueError('Recording JSON requires version: 1')
            payload = payload.get('samples')
        if not isinstance(payload, list) or not payload: raise ValueError('JSON must contain a nonempty sample array')
        df = pd.DataFrame(payload)
    else:
        try: text = raw.decode('utf-8-sig')
        except UnicodeDecodeError: text = raw.decode('latin1')
        df = pd.read_csv(io.StringIO(text), low_memory=False)
    df.columns = [str(c).strip() for c in df.columns]
    if len(df) < 2: raise ValueError('At least two samples are required')
    if len(df) > 2_000_000: raise ValueError('Recording exceeds two million samples; split it into sessions')
    return df

def suggest_mapping(df):
    mapping = {}
    for key in REQUIRED + OPTIONAL:
        if key in df.columns: mapping[key] = key
        else:
            matches = [c for c in df.columns if c.upper().startswith(PREFIXES[key].upper())]
            if matches: mapping[key] = matches[0]
    return mapping

def preview(path):
    df = read_table(path)
    mapping = suggest_mapping(df)
    return {'columns': list(df.columns), 'rows': len(df), 'preview': df.head(6).astype(object).where(pd.notnull(df.head(6)), None).to_dict('records'), 'mapping': mapping,
            'time_unit': 'ms' if mapping.get('t', '').startswith('TIME SINCE') else 's', 'gyro_unit': 'rad/s',
            'missing_required': [k for k in REQUIRED if k not in mapping], 'segments': segments(df, mapping)}

def segments(df, mapping):
    if 't' not in mapping: return []
    values=pd.to_numeric(df[mapping['t']],errors='coerce').to_numpy()
    edges=np.r_[0,np.where(np.diff(values)<=0)[0]+1,len(values)]
    return [{'index':i,'start_row':int(a),'end_row':int(b),'rows':int(b-a)} for i,(a,b) in enumerate(zip(edges[:-1],edges[1:]))]

def normalize(path, mapping=None, time_unit='s', gyro_unit='rad/s', segment=None):
    df = read_table(path)
    columns = mapping or suggest_mapping(df)
    missing = [k for k in REQUIRED if k not in columns or columns[k] not in df.columns]
    if missing: raise ValueError('Map required columns: ' + ', '.join(missing))
    parts=segments(df,columns)
    if segment is not None:
        if segment < 0 or segment >= len(parts): raise ValueError('Invalid recording segment')
        selected=parts[segment];df=df.iloc[selected['start_row']:selected['end_row']].copy()
    out = pd.DataFrame({k: pd.to_numeric(df[v], errors='coerce') for k, v in columns.items() if k in REQUIRED + OPTIONAL and v in df.columns})
    if not np.isfinite(out[REQUIRED].to_numpy()).all(): raise ValueError('IMU samples and timestamps must be finite numbers; inspect missing/invalid rows')
    delta = np.diff(out.t.to_numpy())
    if (delta <= 0).any(): raise ValueError('Timestamps must strictly increase; duplicate or out-of-order samples found')
    out['t'] = (out.t - out.t.iloc[0]) / {'s': 1, 'ms': 1000, 'ns': 1e9}[time_unit]
    if gyro_unit == 'deg/s': out[['gx', 'gy', 'gz']] *= np.pi / 180
    if columns.get('speed', '').startswith('GPS SPEED'): out['speed'] /= 3.6
    for key in OPTIONAL:
        if key not in out: out[key] = np.nan
    out.loc[(out.lat.abs() > 85) | (out.lng.abs() > 180), ['lat', 'lng']] = np.nan
    out.loc[(out.speed < 0) | (out.speed > 100), 'speed'] = np.nan
    out.loc[(out.accuracy < 0) | (out.accuracy > 100), ['lat','lng','speed','heading']] = np.nan
    # A low-pass anti-alias filter cannot recover content already aliased in the source.
    intervals = np.diff(out.t)
    warnings = []
    if intervals.max() > 2: warnings.append('Gaps above 2 seconds: integration pauses until a usable GPS fix; windows crossing gaps are excluded from training.')
    if np.median(intervals) >= 0.09: warnings.append('Approximately 10 Hz recording; vibration above 5 Hz is not resolvable.')
    if out[['lat','lng']].isna().any().any(): warnings.append('Some samples lack GPS reference; accuracy is evaluated only at valid fixes.')
    if out[['gravity_x','gravity_y','gravity_z']].isna().all().all(): warnings.append('No gravity channel: initial attitude requires a stationary start or saved calibration.')
    report = {'rows':len(out), 'duration_s':float(out.t.iloc[-1]), 'sample_rate_hz':float(1/np.median(intervals)),
              'max_gap_s':float(intervals.max()), 'reference_samples':int(out.lat.notna().sum()), 'warnings':warnings,
              'units':{'t':'s','acceleration':'m/s²','gyro':'rad/s','speed':'m/s','position':'WGS84 degrees'}, 'adapter_version':1,'segment':segment,'source_segments':parts}
    return out, report

def save_normalized(df, dataset_id):
    target = DATA / 'processed' / f'{dataset_id}.csv'
    df.to_csv(target, index=False, float_format='%.10g')
    return str(target.relative_to(DATA))

def load_dataset(record):
    return pd.read_csv(DATA / record.data['processed_path'])

def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
