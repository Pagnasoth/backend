#!/usr/bin/env python3
import json
import os
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj, code=200):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/health"):
            self._send_json({"status": "ok"})
        else:
            self._send_json({"error": "not found"}, code=404)

    def do_POST(self):
        if self.path.startswith("/api/analyze"):
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b""
            try:
                payload = json.loads(raw.decode("utf-8")) if raw else {}
            except Exception:
                return self._send_json({"error": "invalid json"}, code=400)

            code = payload.get("code") or ""
            language = payload.get("language") or payload.get("lang") or "unknown"
            model = payload.get("model") or "Gemini"

            if not code.strip():
                return self._send_json({"error": "No code provided"}, code=400)

            mock = (
                f"🔍 Mock Analysis (simple server)\n\nLanguage: {language}\nModel: {model}\n\n"
                "Found 2 potential issues:\n\n"
                "1. Line 3: Missing error handling for async operation → Add try-catch block.\n"
                "2. Line 7: Unused variable 'temp' → Remove or use the variable.\n"
                "\nHint: To enable real Gemini calls, run the FastAPI server with GEMINI_API_KEY and GEMINI_API_URL."
            )

            return self._send_json({"result": mock})

        return self._send_json({"error": "not found"}, code=404)


def run(host: str, port: int):
    server = HTTPServer((host, port), Handler)
    print(f"Simple server listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down")
        server.server_close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=5174)
    args = p.parse_args()
    run(args.host, args.port)
