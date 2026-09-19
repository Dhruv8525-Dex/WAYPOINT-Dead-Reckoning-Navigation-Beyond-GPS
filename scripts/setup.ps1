param([string]$PythonPath='', [switch]$Cuda)
$ErrorActionPreference='Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (!(Test-Path .venv/Scripts/python.exe)) {
 if (!$PythonPath) { $PythonPath=Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' }
 if (!(Test-Path -LiteralPath $PythonPath)) { throw 'Supply -PythonPath pointing to Python 3.12.' }
 & $PythonPath -m venv .venv
 if ($LASTEXITCODE) { throw 'Python environment creation failed' }
}
& .venv/Scripts/python.exe -m pip install -r backend/requirements-lock.txt
if ($LASTEXITCODE) { throw 'Backend dependency installation failed' }
if ($Cuda) { & .venv/Scripts/python.exe -m pip install torch==2.7.0 --index-url https://download.pytorch.org/whl/cu118 }
else { & .venv/Scripts/python.exe -m pip install torch==2.7.0 --index-url https://download.pytorch.org/whl/cpu }
if ($LASTEXITCODE) { throw 'PyTorch installation failed' }
npm ci
if ($LASTEXITCODE) { throw 'Frontend dependency installation failed' }
& .venv/Scripts/python.exe -c 'from backend.waypoint.db import migrate;migrate()'
Write-Host 'Ready. Run npm run dev (or npm run dev -- --lan for phone pairing).'
