import {spawnSync} from 'node:child_process';
const result=spawnSync('.venv/Scripts/python.exe',['-m','pytest','backend/tests','-q'],{stdio:'inherit',windowsHide:true});process.exit(result.status||0);
