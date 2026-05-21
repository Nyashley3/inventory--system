#!/usr/bin/env pwsh
# One-command PowerShell launcher for the Inventory app.
# - Creates virtualenv if missing
# - Installs requirements
# - Runs the app using the venv python executable

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $root
$py = Join-Path $root 'venv\Scripts\python.exe'
if (-not (Test-Path $py)) {
  Write-Host "Creating virtual environment..."
  python -m venv venv
}
Write-Host "Installing requirements (may skip if already installed)..."
& "$py" -m pip install --upgrade pip
& "$py" -m pip install -r requirements.txt
Write-Host "Starting Inventory app..."
& "$py" app.py
