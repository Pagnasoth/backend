# Lets-Run Backend (Python)

This repo ships a Python FastAPI backend that provides the `/api/analyze` endpoint expected by the frontend. The Python backend runs on port `5174` by default so the Vite proxy does not require changes.

Setup (Python)

1. Create and activate a virtual environment (recommended):

```bash
cd D:\\Let's-Run\\Let's-Run-in-Peace\\backend
python -m venv .venv
# Unix/macOS:
source .venv/bin/activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1
```

2. Install Python dependencies:

```bash
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
```

3. Configure environment:

Copy `.env.example` to `.env` and set `GEMINI_API_KEY` and `GEMINI_API_URL` (do not commit this file).

4. Run the Python dev server:

```bash
.venv\Scripts\python -m uvicorn app:app --reload --port 8000
```

## Run helper scripts (Windows)

If you're on Windows, two helper scripts are included in the `backend/` folder:

- `run.ps1` — PowerShell script that creates `.venv`, installs requirements, and runs the server.
- `run.bat` — equivalent batch script for cmd.exe.

From PowerShell (recommended):

```powershell
cd /d "D:\\Let's-Run\\Let's-Run-in-Peace\\backend"
./run.ps1
```

From cmd.exe:

```cmd
cd /d D:\\Let's-Run\\Let's-Run-in-Peace\\backend
run.bat
```

Behavior

- If `GEMINI_API_KEY` and `GEMINI_API_URL` are set and the URL points to Google Generative Language, the server will attempt to call it and return the provider's result.
- If credentials are not set, the server returns a mocked analysis so the frontend remains functional for development.
