import argparse
import json
import shutil
from pathlib import Path
from backend.waypoint.db import migrate,Session,Project,Record,Job,uid,record_dict
from backend.waypoint.config import DATA,ROOT
from backend.waypoint.ingest import normalize,checksum,save_normalized,preview

def main():
    migrate()
    with Session() as db:
        project=db.query(Project).filter_by(name='IO-VNBD research').first()
        if not project:
            project=Project(name='IO-VNBD research',description='Independent real-world recordings. Train S1, validate S2, test S4.');db.add(project);db.commit()
        ids={}
        for seq in (1,2,4):
            name=f'IO-VNBD S{seq}';record=db.query(Record).filter_by(project_id=project.id,kind='dataset',name=name).first()
            if not record:
                source=ROOT/'data'/'raw'/f'S-S{seq}.csv';parts=preview(source)['segments'];segment=max(parts,key=lambda p:p['rows'])['index'];df,report=normalize(source,time_unit='ms',segment=segment);id=uid();raw=DATA/'raw'/f'{id}.csv';shutil.copyfile(source,raw)
                record=Record(id=id,kind='dataset',project_id=project.id,name=name,data={**report,'checksum':checksum(source),'raw_path':str(raw.relative_to(DATA)), 'processed_path':save_normalized(df,id), 'source':'https://github.com/onyekpeu/IO-VNBD','time_unit':'ms','gyro_unit':'rad/s'})
                db.add(record);db.commit()
            ids[seq]=record.id
        print(json.dumps({'project_id':project.id,'datasets':ids}),flush=True)
        (ROOT/'artifacts'/'seed.json').write_text(json.dumps({'project_id':project.id,'datasets':ids}))
        if '--train' in __import__('sys').argv:
            for architecture in ('ridge','cnn_gru'):
                config={'project_id':project.id,'name':f'{architecture} · S1 / S2 / S4','train_ids':[ids[1]],'validation_ids':[ids[2]],'test_ids':[ids[4]],'architecture':architecture,'epochs':20,'seed':42}
                if not db.query(Job).filter_by(kind='training',config=config).first():
                    db.add(Job(project_id=project.id,kind='training',config=config));db.commit()
if __name__=='__main__':main()
