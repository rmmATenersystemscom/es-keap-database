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
        # Metrics tracking
        self.last_throttle_remaining = None
        self.last_throttle_type = None
        self.last_retry_count = 0
        self.last_response_size = None

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
        
        # Track metrics
        self.last_response_size = len(r.content)
        self.last_retry_count = getattr(r, 'retry_count', 0)
        
        # Enhanced throttle handling
        self._handle_throttle_headers(r)
        
        if r.status_code == 401 and not self.cfg.api_key:
            tb = load_token_bundle(self.cfg)
            if tb:
                tb = refresh_tokens(self.cfg, tb.refresh_token)
                save_token_bundle(self.cfg, tb)
                r = self.session.request(method, url, headers=self._headers(), timeout=60, **kwargs)
        r.raise_for_status()
        return r
    
    def _handle_throttle_headers(self, response: requests.Response) -> None:
        """Handle Keap throttle headers and implement appropriate backoff."""
        headers = response.headers
        
        # Check various throttle headers
        throttle_headers = {
            'x-keap-product-throttle-available': 'product',
            'x-keap-api-throttle-available': 'api',
            'x-keap-rate-limit-remaining': 'rate_limit',
            'x-ratelimit-remaining': 'rate_limit_alt'
        }
        
        min_available = float('inf')
        throttle_type = None
        
        for header, throttle_name in throttle_headers.items():
            if header in headers:
                try:
                    available = int(headers[header])
                    if available < min_available:
                        min_available = available
                        throttle_type = throttle_name
                except (ValueError, TypeError):
                    continue
        
        # Track throttle metrics
        self.last_throttle_remaining = int(min_available) if min_available != float('inf') else None
        self.last_throttle_type = throttle_type
        
        # Implement backoff based on throttle status
        if min_available != float('inf'):
            if min_available < 10:
                # Critical throttle - wait longer
                wait_time = 5.0
                print(f"Critical throttle detected ({throttle_type}: {min_available}), waiting {wait_time}s")
                time.sleep(wait_time)
            elif min_available < 50:
                # Low throttle - moderate wait
                wait_time = 2.0
                print(f"Low throttle detected ({throttle_type}: {min_available}), waiting {wait_time}s")
                time.sleep(wait_time)
            elif min_available < 100:
                # Medium throttle - short wait
                wait_time = 0.5
                print(f"Medium throttle detected ({throttle_type}: {min_available}), waiting {wait_time}s")
                time.sleep(wait_time)
            else:
                # Good throttle level - no wait needed
                pass

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
