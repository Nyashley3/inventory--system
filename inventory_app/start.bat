@echo off
rem One-command batch launcher for Windows
cd /d %~dp0
if not exist venv\Scripts\python.exe (
  echo Creating virtual environment...
  python -m venv venv
)
echo Installing requirements (may skip if already installed)...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt
echo Starting Inventory app...
venv\Scripts\python.exe app.py
