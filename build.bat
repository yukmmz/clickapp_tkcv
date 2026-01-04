@echo off
if not exist .venv (
    echo making virtual environment...
    python3.12 -m venv .venv
)
echo Checking and installing libraries...
.venv\Scripts\python -m pip install -r requirements.txt

echo Press any key to continue...
pause >nul