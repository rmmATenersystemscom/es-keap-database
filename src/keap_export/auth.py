from __future__ import annotations
import json, time, urllib.parse
import requests
from dataclasses import dataclass
from .config import Settings, load_tokens

AUTH_URL = "https://accounts.infusionsoft.com/app/oauth/authorize"
TOKEN_URL = "https://api.infusionsoft.com/token"

@dataclass
class TokenBundle:
    access_token: str
    refresh_token: str
    expires_at: float  # epoch seconds

    @property
    def is_expired(self) -> bool:
        return time.time() >= self.expires_at - 60

def build_authorize_url(cfg: Settings, state: str = "keap_export") -> str:
    params = {
        "client_id": cfg.client_id,
        "redirect_uri": cfg.redirect_uri,
        "response_type": "code",
        "scope": "full",
        "state": state,
    }
    return AUTH_URL + "?" + urllib.parse.urlencode(params)

def exchange_code_for_tokens(cfg: Settings, code: str) -> TokenBundle:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": cfg.redirect_uri,
        "client_id": cfg.client_id,
        "client_secret": cfg.client_secret,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(TOKEN_URL, data=data, headers=headers, timeout=30)
    r.raise_for_status()
    js = r.json()
    return TokenBundle(
        access_token=js["access_token"],
        refresh_token=js["refresh_token"],
        expires_at=time.time() + int(js.get("expires_in", 3000)),
    )

def refresh_tokens(cfg: Settings, refresh_token: str) -> TokenBundle:
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": cfg.client_id,
        "client_secret": cfg.client_secret,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(TOKEN_URL, data=data, headers=headers, timeout=30)
    r.raise_for_status()
    js = r.json()
    return TokenBundle(
        access_token=js["access_token"],
        refresh_token=js["refresh_token"],
        expires_at=time.time() + int(js.get("expires_in", 3000)),
    )

def load_token_bundle(cfg: Settings) -> TokenBundle | None:
    js = load_tokens(cfg.token_file)
    if not js:
        return None
    return TokenBundle(js["access_token"], js["refresh_token"], js["expires_at"])

def save_token_bundle(cfg: Settings, tb: TokenBundle) -> None:
    with open(cfg.token_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "access_token": tb.access_token,
                "refresh_token": tb.refresh_token,
                "expires_at": tb.expires_at,
            },
            f,
            indent=2,
        )
