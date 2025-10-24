#!/usr/bin/env python3
from __future__ import annotations
import http.server, socketserver, urllib.parse, os, sys

# Ensure project src is importable (adjust if different path)
sys.path.insert(0, "/opt/es-keap-database/src")

from keap_export.config import Settings
from keap_export.auth import exchange_code_for_tokens, save_token_bundle

PORT = int(os.getenv("OAUTH_PORT", "5000"))
CALLBACK_PATH = os.getenv("OAUTH_CALLBACK_PATH", "/keap/oauth/callback")
ALLOWED_STATE = os.getenv("OAUTH_ALLOWED_STATE")  # optional CSRF state check

cfg = Settings()  # reads .env in /opt/es-keap-database

class Handler(http.server.BaseHTTPRequestHandler):
    def _write(self, status:int, body:str):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/health":
            return self._write(200, "ok")
        if parsed.path != CALLBACK_PATH:
            return self._write(404, "Not Found")
        qs = urllib.parse.parse_qs(parsed.query or "")
        code = (qs.get("code") or [None])[0]
        state = (qs.get("state") or [None])[0]
        if not code:
            return self._write(400, "Missing code")
        if ALLOWED_STATE and state != ALLOWED_STATE:
            return self._write(400, "Invalid state")
        try:
            tb = exchange_code_for_tokens(cfg, code)
            save_token_bundle(cfg, tb)
        except Exception as e:
            return self._write(500, f"Token exchange failed: {e}")
        return self._write(200, "Keap auth complete. You can close this tab.")

if __name__ == "__main__":
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"Callback server listening on http://127.0.0.1:{PORT}{CALLBACK_PATH}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
