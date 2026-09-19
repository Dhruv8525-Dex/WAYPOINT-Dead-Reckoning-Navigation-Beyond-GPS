param([Parameter(Mandatory=$true)][string]$Archive,[Parameter(Mandatory=$true)][string]$Destination)
$ErrorActionPreference='Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
& .venv/Scripts/python.exe -m scripts.restore_cli $Archive $Destination
if ($LASTEXITCODE) { throw 'Restore failed; existing workspace was not overwritten.' }
