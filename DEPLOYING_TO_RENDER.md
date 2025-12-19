# Deploying to Render ✅

You can deploy this FastAPI service on Render as a **Web Service**.

**Quick steps:**

1. Push this repo to GitHub and connect it to Render.
2. Use the included `render.yaml` (or configure a new Web Service in the Render dashboard):
   - **buildCommand:** `pip install -r requirements.txt`
   - **startCommand:** `uvicorn app:app --host 0.0.0.0 --port $PORT --proxy-headers`
3. Add the required environment variables in Render (do **not** commit secrets):
   - `GEMINI_API_KEY` (recommended)
   - `GEMINI_API_URL` (optional)
   - `OPENAI_API_KEY` (optional)
4. Deploy — Render will install dependencies from `requirements.txt` and run the start command.

**Notes & troubleshooting:**

- The service exposes `/health` (simple healthcheck) and `/api/debug` (admin/debug info).
- If you're using Google Gemini via the `google-genai` Python client, ensure `google-genai` is installed (e.g., `google-genai>=0.8.0`).
- For local testing you can run `python -m app` (will pick up `$PORT`), or use `uvicorn app:app --reload --port 8000`.
- If you need to change the server command, update `render.yaml` or the `Procfile`.
