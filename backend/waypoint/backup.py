"""Offline, consistent workspace backup and restore."""
from pathlib import Path
from contextlib import closing
import hashlib
import json
import sqlite3
import tempfile
import zipfile
import shutil
from .config import DATA

def backup():
    target=DATA.parent/'waypoint-backup.zip'
    with tempfile.TemporaryDirectory() as temporary:
        snapshot=Path(temporary)/'waypoint.db'
        with closing(sqlite3.connect(DATA/'waypoint.db')) as source, closing(sqlite3.connect(snapshot)) as destination: source.backup(destination)
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
            hashes={}
            for path in [snapshot]+[p for p in DATA.rglob('*') if p.is_file() and p.name not in ('waypoint.db','waypoint.db-wal','waypoint.db-shm')]:
                relative='waypoint.db' if path==snapshot else path.relative_to(DATA).as_posix()
                archive.write(path,relative);hashes[relative]=hashlib.sha256(path.read_bytes()).hexdigest()
            archive.writestr('backup-manifest.json',json.dumps({'version':1,'sha256':hashes}))
    return target

def restore(archive_path, destination):
    destination=Path(destination).resolve()
    if destination.exists() and any(destination.iterdir()): raise ValueError('Restore into a new empty directory; preserve the current workspace')
    with zipfile.ZipFile(archive_path) as archive:
        if sum(i.file_size for i in archive.infolist())>5*1024**3: raise ValueError('Backup exceeds 5 GB restore limit')
        manifest=json.loads(archive.read('backup-manifest.json'))
        if manifest.get('version')!=1: raise ValueError('Unsupported backup version')
        for info in archive.infolist():
            target=(destination/info.filename).resolve()
            if not target.is_relative_to(destination): raise ValueError('Unsafe archive path')
            if info.filename!='backup-manifest.json':
                if info.filename not in manifest['sha256'] or hashlib.sha256(archive.read(info)).hexdigest()!=manifest['sha256'][info.filename]: raise ValueError('Backup checksum mismatch')
        archive.extractall(destination)
    with closing(sqlite3.connect(destination/'waypoint.db')) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise ValueError('Database integrity check failed')
        # A restored workspace must re-pair phones; old secrets are intentionally invalidated.
        db.execute('UPDATE devices SET revoked=1');db.commit()
    return destination
