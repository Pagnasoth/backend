@echo off
REM Windows batch helper to create venv, install requirements, and run the FastAPI server.
IF NOT DEFINED PYTHON_EXEC (SET PYTHON_EXEC=python)

%PYTHON_EXEC% -V >nul 2>&1
IF ERRORLEVEL 1 (
  echo Python not found. Please install Python 3.11+ and ensure 'python' is on PATH.
  exit /b 1
)

IF NOT EXIST .venv (
  echo Creating virtual environment (.venv)...
  %PYTHON_EXEC% -m venv .venv
)

SET VENV_PY=.venv\Scripts\python.exe
IF NOT EXIST %VENV_PY% (
  echo Virtual env python not found at %VENV_PY%
  exit /b 1
)

echo Upgrading pip and installing requirements...
%VENV_PY% -m pip install --upgrade pip
%VENV_PY% -m pip install -r requirements-python.txt

echo Starting FastAPI (uvicorn) on http://localhost:5174
%VENV_PY% -m uvicorn app:app --reload --port 5174
