import psutil
from backend.waypoint.db import Session,Job
with Session() as db:
    for j in db.query(Job).filter_by(kind='run'):
        if j.status=='queued':j.status='cancelled';j.message='Superseded by corrected engine validation'
    db.commit()
for connection in psutil.net_connections('tcp'):
    if connection.laddr and connection.laddr.port==8000 and connection.status=='LISTEN':
        process=psutil.Process(connection.pid)
        if 'backend.waypoint.launch' in ' '.join(process.cmdline()):
            for child in process.children(recursive=True):child.terminate()
            process.terminate()
