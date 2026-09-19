import { spawn } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const data = mkdtempSync(join(tmpdir(), 'waypoint-browser-'));
const python = process.platform === 'win32' ? '.venv/Scripts/python.exe' : 'python';
const child = spawn(python, ['-m', 'backend.waypoint.launch'], {
  stdio: 'inherit',
  env: { ...process.env, WAYPOINT_DATA: data, WAYPOINT_NO_WORKER: '1' },
});
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill(signal));
child.on('exit', code => process.exit(code ?? 0));
