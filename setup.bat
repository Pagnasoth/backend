@echo off
REM Setup script for Python backend on Windows
cd /d "%~dp0"
echo.
echo Creating Python virtual environment...
python3 -m venv .venv
if errorlevel 1 (
    echo Failed to create venv. Trying alternative...
    python -m venv .venv
)

echo.
echo Upgrading pip...
call .venv\Scripts\python -m pip install --upgrade pip

echo.
echo Installing requirements...
call .venv\Scripts\python -m pip install -r requirements-python.txt

echo.
echo Setup complete! You can now run the server with:
echo   .venv\Scripts\python -m uvicorn app:app --reload --port 8000
pause
