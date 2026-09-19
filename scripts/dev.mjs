import {spawn} from 'node:child_process';
import {existsSync} from 'node:fs';
import {resolve} from 'node:path';
const python=resolve('.venv/Scripts/python.exe');
if(!existsSync(python)){console.error('Run scripts/setup.ps1 first.');process.exit(1)}
const children=[];
try { const response=await fetch('http://127.0.0.1:8000/api/v1/health'); if(!response.ok)throw Error(); }
catch { children.push(spawn(python,['-m','backend.waypoint.launch',...(process.argv.includes('--lan')?['--lan']:[])],{stdio:'inherit',windowsHide:true})); }
children.push(spawn(process.execPath,['node_modules/vite/bin/vite.js'],{stdio:'inherit',windowsHide:true}));
const stop=()=>{for(const child of children)child.kill();process.exit()};process.on('SIGINT',stop);process.on('SIGTERM',stop);
