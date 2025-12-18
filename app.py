from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
# Allow explicit override via env; otherwise auto-detect based on key
GEMINI_API_URL = os.getenv('GEMINI_API_URL') or None
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Candidate models to try (priority order)
_GEMINI_CANDIDATE_MODELS = [
    'gemini-2.5-flash'
]


def _detect_gemini_model():
    """Try candidate models using the API key and pick the first that the
    service recognizes. Cache the result to avoid repeated probing.
    """
    if not GEMINI_API_KEY:
        return None

    cache_path = os.path.join(os.path.dirname(__file__), 'gemini_detected_model.txt')
    try:
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                model = f.read().strip()
                if model:
                    return f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
    except Exception:
        pass

    # Minimal probe body (very small prompt to limit token use)
    probe_body = {'contents': [{'parts': [{'text': 'Ping'}]}]}

    for candidate in _GEMINI_CANDIDATE_MODELS:
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{candidate}:generateContent'
        params = {'key': GEMINI_API_KEY}
        try:
            resp = requests.post(url, params=params, json=probe_body, timeout=5)
            # Accept this candidate if the service responds with anything
            # other than 401 (unauthorized) or 404 (model not found).
            if resp.status_code not in (401, 404):
                try:
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        f.write(candidate)
                except Exception:
                    pass
                return url
        except requests.RequestException:
            # network/timeout - try next candidate
            continue

    return None


def _extract_model_from_url(url: Optional[str]):
    """Extract the model id from a Google generative language URL."""
    try:
        if not url:
            return None
        if 'models/' in url:
            segment = url.split('models/', 1)[1]
            segment = segment.split(':', 1)[0]
            return segment.strip() or None
    except Exception:
        return None
    return None

# Auto-detect model URL if not provided explicitly
if GEMINI_API_URL is None:
    detected = _detect_gemini_model()
    GEMINI_API_URL = detected or 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'

app = FastAPI()


class AnalyzeRequest(BaseModel):
    code: str
    language: Optional[str] = None
    model: Optional[str] = 'Gemini'


# Helper to append debug logs for Gemini requests/responses
def _gemini_log(message: str):
    try:
        from datetime import datetime
        log_path = os.path.join(os.path.dirname(__file__), 'gemini_debug.log')
        ts = datetime.utcnow().isoformat() + 'Z'
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {message}\n")
    except Exception:
        pass


def _build_mock_analysis(reason: str, req: AnalyzeRequest):
    """Consistent mock response when the real provider is unavailable."""
    return (
        f"🔍 Mock Analysis ({reason})\n\nLanguage: {req.language or 'unknown'}\nModel: {req.model or 'Gemini'}\n\n"
        "Found 2 potential issues:\n\n1. Line 3: Missing error handling for async operation → Add try-catch block.\n"
        "2. Line 7: Unused variable 'temp' → Remove or use the variable.\n"
    )


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.get('/favicon.ico')
def favicon():
    # Return no content to avoid 404 logs from browsers requesting favicon
    return Response(status_code=204)


@app.get('/api/admin')
def admin_status():
    """Return detected model and recent debug errors for troubleshooting."""
    status = {
        'gemini_api_key_set': bool(GEMINI_API_KEY),
        'gemini_api_url': GEMINI_API_URL,
        'detected_model_cache': None,
        'recent_errors': []
    }
    
    cache_path = os.path.join(os.path.dirname(__file__), 'gemini_detected_model.txt')
    try:
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                status['detected_model_cache'] = f.read().strip()
    except Exception:
        pass
    
    log_path = os.path.join(os.path.dirname(__file__), 'gemini_debug.log')
    try:
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                errors = [l.strip() for l in lines if 'EXCEPTION' in l][-20:]
                status['recent_errors'] = errors
    except Exception:
        pass
    
    return status


@app.get('/api/models')
def get_models():
    """Return list of available Gemini models for the frontend dropdown.
    Surfaces the detected model tied to the configured API key when possible.
    """
    models = []

    detected_model = _extract_model_from_url(GEMINI_API_URL)
    if not detected_model:
        try:
            cache_path = os.path.join(os.path.dirname(__file__), 'gemini_detected_model.txt')
            if os.path.exists(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    detected_model = f.read().strip() or None
        except Exception:
            pass

    if GEMINI_API_KEY:
        if detected_model:
            models.append({
                'value': detected_model,
                'label': f"{detected_model} (Gemini, via API key)"
            })
        else:
            models.append({
                'value': 'gemini-2.0-flash',
                'label': 'Gemini 2.0 Flash (fallback, API key set)'
            })
    else:
        models.append({
            'value': 'gemini-2.0-flash',
            'label': 'Gemini 2.0 Flash (mock; no API key)'
        })

    # Add remaining candidates for manual selection
    existing_values = set([m['value'] for m in models])
    for candidate in _GEMINI_CANDIDATE_MODELS:
        if candidate in existing_values:
            continue
        models.append({
            'value': candidate,
            'label': candidate.replace('-', ' ').title() + ' (Gemini)'
        })
        existing_values.add(candidate)

    return {'models': models}


def call_gemini_google(prompt: str):
    """Call Google Gemini using the google.genai Python client (single attempt) following the recommended client pattern."""
    try:
        from google import genai
    except Exception as e:
        _gemini_log(f"EXCEPTION importing google.genai: {e}")
        raise RuntimeError("google.genai not available; install google-genai") from e

    # Instantiate client (pass api_key if available)
    try:
        client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else genai.Client()
    except TypeError:
        # Older/newer versions may not accept api_key kwarg - fallback
        client = genai.Client()

    model = 'gemini-2.5-flash'
    _gemini_log(f"REQUEST to genai model={model} prompt_length={len(prompt)}")

    try:
        # Use the recommended pattern: client.models.generate_content
        response = client.models.generate_content(model=model, contents=prompt)
        _gemini_log(f"RESPONSE from genai: {response}")

        # Common response shapes: check for 'output_text', 'text', or structured 'output'
        text = getattr(response, 'output_text', None) or getattr(response, 'text', None)
        if text:
            return text
        if hasattr(response, 'output') and response.output:
            try:
                # Some clients return output items with a 'content' field
                return response.output[0].content
            except Exception:
                return str(response)
        # Fallback
        return str(response)

    except Exception as e:
        print("Exception calling genai generate_content:", e)
        _gemini_log(f"EXCEPTION calling genai generate_content: {e}")
        raise


@app.get('/api/debug')
def debug_status():
    """Admin endpoint: show detected model, provider status, and last errors."""
    detected_model = None
    try:
        cache_path = os.path.join(os.path.dirname(__file__), 'gemini_detected_model.txt')
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                detected_model = f.read().strip()
    except Exception:
        pass

    last_error = None
    try:
        log_path = os.path.join(os.path.dirname(__file__), 'gemini_debug.log')
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in reversed(lines[-20:]):
                    if 'EXCEPTION' in line or 'error' in line.lower():
                        last_error = line.strip()
                        break
    except Exception:
        pass

    return {
        'status': 'debug',
        'gemini_api_key': 'configured' if GEMINI_API_KEY else 'missing',
        'gemini_api_url': GEMINI_API_URL,
        'gemini_detected_model': detected_model,
        'openai_api_key': 'configured' if OPENAI_API_KEY else 'missing',
        'last_error': last_error,
        'fallback_chain': ['Gemini', 'OpenAI'] if OPENAI_API_KEY else ['Gemini', 'Mock']
    }


@app.post('/api/analyze')
def analyze(req: AnalyzeRequest):
    if not req.code or not req.code.strip():
        raise HTTPException(status_code=400, detail='No code provided')

    prompt = f"Analyze the following {req.language or 'code'} for security issues and return a concise report:\n\n{req.code}"
    print(prompt)

    # If credentials are provided and URL looks like Google API, call it
    if GEMINI_API_KEY:
        print("Catch the fish")
        try:
            result = call_gemini_google(prompt)
            return {'result': result}
        except Exception as e:
            _gemini_log(f"Top-level handler caught exception: {str(e)}")
            reason = "Gemini rate limit hit; showing mock analysis" if '429' in str(e) else "Gemini unavailable; showing mock analysis"
            return {'result': _build_mock_analysis(reason, req)}

    # Generic provider path
    if GEMINI_API_KEY and GEMINI_API_URL and 'generativelanguage.googleapis.com' not in GEMINI_API_URL:
        print("Catch the other fish")
        try:
            headers = {'Content-Type': 'application/json'}
            headers['Authorization'] = f'Bearer {GEMINI_API_KEY}'
            body = {'model': req.model or 'gemini', 'prompt': prompt}
            try:
                _gemini_log(f"REQUEST to {GEMINI_API_URL} headers={{'Authorization': 'Bearer <REDACTED>'}} body={body}")
                resp = requests.post(GEMINI_API_URL, json=body, headers=headers, timeout=30)
                _gemini_log(f"RESPONSE status={resp.status_code} text={resp.text}")
                resp.raise_for_status()
                j = resp.json()
            except Exception as e:
                _gemini_log(f"EXCEPTION calling generic provider: {str(e)}")
                try:
                    _gemini_log(f"EXCEPTION response_text: {getattr(e, 'response').text}")
                except Exception:
                    pass
                raise
            # Best-effort extraction
            return {'result': j.get('result') or str(j)}
        except Exception as e:
            _gemini_log(f"Generic provider error: {str(e)}")
            return {'result': _build_mock_analysis("Provider unavailable; showing mock analysis", req)}

    # Fallback mocked analysis
    return {'result': _build_mock_analysis("no Gemini credentials configured", req)}
