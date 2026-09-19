import {spawn} from 'node:child_process';
import {existsSync} from 'node:fs';
if(!existsSync('dist/index.html')){console.error('Run npm run build first.');process.exit(1)}
const child=spawn('.venv/Scripts/python.exe',['-m','backend.waypoint.launch',...(process.argv.includes('--lan')?['--lan']:[])],{stdio:'inherit',windowsHide:true});child.on('exit',code=>process.exit(code||0));process.on('SIGINT',()=>child.kill());
