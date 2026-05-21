#!/usr/bin/env pwsh
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $root
$py = Join-Path $root 'venv\Scripts\python.exe'
if (-not (Test-Path $py)) {
  Write-Host "Creating virtual environment..."
  python -m venv venv
}
Write-Host "Installing requirements..."
& "$py" -m pip install --upgrade pip
& "$py" -m pip install -r requirements.txt
Write-Host "Running admin initialization helper..."
& "$py" .\init_admin.py @args
