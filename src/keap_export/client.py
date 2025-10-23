from __future__ import annotations
import time, typing as t
import requests
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from .config import Settings
from .auth import load_token_bundle, refresh_tokens, save_token_bundle

class KeapClient:
    def __init__(self, cfg: Settings):
        self.cfg = cfg
        self.session = requests.Session()
        self.base = cfg.base_url.rstrip("/")

    def _headers(self) -> dict:
        headers = {"Accept": "application/json"}
        if self.cfg.api_key:
            headers["X-Keap-API-Key"] = self.cfg.api_key
        else:
            tb = load_token_bundle(self.cfg)
            if not tb:
                raise RuntimeError("No OAuth tokens found. Run initial auth to create token file.")
            if tb.is_expired:
                tb = refresh_tokens(self.cfg, tb.refresh_token)
                save_token_bundle(self.cfg, tb)
            headers["Authorization"] = f"Bearer {tb.access_token}"
        return headers

    @retry(stop=stop_after_attempt(5), wait=wait_exponential_jitter(initial=1, max=30))
    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = self.base + path
        r = self.session.request(method, url, headers=self._headers(), timeout=60, **kwargs)
        # Soft-throttle: if headers indicate low budget, sleep a bit
        try:
            avail = int(r.headers.get("x-keap-product-throttle-available", "1000"))
            if avail < 50:
                time.sleep(1.0)
        except ValueError:
            pass
        if r.status_code == 401 and not self.cfg.api_key:
            tb = load_token_bundle(self.cfg)
            if tb:
                tb = refresh_tokens(self.cfg, tb.refresh_token)
                save_token_bundle(self.cfg, tb)
                r = self.session.request(method, url, headers=self._headers(), timeout=60, **kwargs)
        r.raise_for_status()
        return r

    def fetch_all(self, path: str, params: dict | None = None, limit: int = 1000):
        """Yield items across limit/offset pagination."""
        p = dict(params or {})
        offset = 0
        while True:
            p.update({"limit": limit, "offset": offset})
            resp = self.request("GET", path, params=p)
            js = resp.json()
            items = js if isinstance(js, list) else js.get("contacts") or js.get("items") or js.get("data")
            if items is None and isinstance(js, list):
                items = js
            if not items:
                break
            for it in items:
                yield it
            if len(items) < limit:
                break
            offset += limit
