from __future__ import annotations
import json
import psycopg2
from .config import Settings

def get_conn(cfg: Settings):
    return psycopg2.connect(
        host=cfg.db_host, port=cfg.db_port, dbname=cfg.db_name, user=cfg.db_user, password=cfg.db_password
    )

def upsert_contact(conn, row: dict):
    """Upsert a contact (example); expand for other tables similarly."""
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into keap.contacts (id, company_id, given_name, family_name, owner_id, emails, phones, addresses, created_at, updated_at, raw)
            values (%(id)s, %(company_id)s, %(given_name)s, %(family_name)s, %(owner_id)s, %(emails)s, %(phones)s, %(addresses)s, %(created_at)s, %(updated_at)s, %(raw)s)
            on conflict (id) do update set
                company_id=excluded.company_id,
                given_name=excluded.given_name,
                family_name=excluded.family_name,
                owner_id=excluded.owner_id,
                emails=excluded.emails,
                phones=excluded.phones,
                addresses=excluded.addresses,
                created_at=excluded.created_at,
                updated_at=excluded.updated_at,
                raw=excluded.raw
            """,
            row,
        )

def to_jsonb(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)
