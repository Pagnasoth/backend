<#
PowerShell helper to create a venv, install requirements, and run the FastAPI server.
Usage: Open PowerShell as normal (not elevated) and run:
  ./run.ps1

This script will:
 - create `.venv` if it doesn't exist
 - install requirements from `requirements-python.txt`
 - start the uvicorn server on port 5174
#>
set-StrictMode -Version Latest

function Abort($msg) {
    Write-Error $msg
    exit 1
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Abort "Python is not found in PATH. Install Python 3.11+ and ensure 'python' is on PATH."
}

if (-not (Test-Path -Path .venv)) {
    Write-Host "Creating virtual environment (.venv)..."
    python -m venv .venv
}

$venvPython = Join-Path -Path $PWD -ChildPath ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Abort "Virtual environment python not found at $venvPython"
}

Write-Host "Upgrading pip and installing requirements..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements-python.txt

Write-Host "Starting FastAPI (uvicorn) on http://localhost:5174"
& $venvPython -m uvicorn app:app --reload --port 8000
