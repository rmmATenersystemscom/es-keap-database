from __future__ import annotations
import os, json
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class Settings:
    base_url: str = os.getenv("KEAP_BASE_URL", "https://api.infusionsoft.com")
    client_id: Optional[str] = os.getenv("KEAP_CLIENT_ID")
    client_secret: Optional[str] = os.getenv("KEAP_CLIENT_SECRET")
    redirect_uri: Optional[str] = os.getenv("KEAP_REDIRECT_URI")
    api_key: Optional[str] = os.getenv("KEAP_API_KEY")
    token_file: str = os.getenv("KEAP_TOKEN_FILE", ".keap_tokens.json")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "json")

    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "keap")
    db_user: str = os.getenv("DB_USER", "keap")
    db_password: str = os.getenv("DB_PASSWORD", "keap")

def load_tokens(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
