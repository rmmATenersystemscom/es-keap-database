from __future__ import annotations
import json
from dotenv import load_dotenv
from keap_export.config import Settings
from keap_export.auth import build_authorize_url, exchange_code_for_tokens, save_token_bundle, load_token_bundle
from keap_export.client import KeapClient

def main():
    load_dotenv()
    cfg = Settings()

    tb = load_token_bundle(cfg)
    if not tb and not cfg.api_key:
        print("No OAuth tokens found and no API key set.")
        print("1) In Keap Developer Portal, set your app's Redirect URI to your HTTPS callback URL.")
        print("2) Open this URL, login, and authorize, then copy the 'code' query param from the redirected URL:")
        print(build_authorize_url(cfg))
        code = input("Paste the 'code' value here: ").strip()
        tb = exchange_code_for_tokens(cfg, code)
        save_token_bundle(cfg, tb)
        print("Saved new tokens to", cfg.token_file)

    client = KeapClient(cfg)
    r = client.request("GET", "/crm/rest/v1/contacts", params={"limit": 5, "offset": 0})
    print(json.dumps(r.json(), indent=2)[:2000])

if __name__ == "__main__":
    main()
