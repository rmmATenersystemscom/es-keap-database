# Keap Exporter (Python) — Starter Kit

This starter gives you a production-ready scaffold to **export all data from Keap**, preserve relationships in **PostgreSQL**, and **validate** each run.

## What’s included
- **User story** and **Implementation story**
- **Project layout**
- **Requirements**
- **Sample Python connection code** (OAuth2 or API Key)
- **Keap API reference (concise)**
- **Validation SQL + ETL meta tables**
- **Cursor master prompt** to ingest all docs and code
- **Makefile** helpers

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create your .env from template
cp .env.example .env
# Fill KEAP_* secrets and DB_*

# Try a connection + list 5 contacts
python src/scripts/sample_connect.py
```

## Postgres schema & validation
Load the schema and validation aids:
```bash
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sql/schema.sql
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sql/keap_etl_support.sql
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sql/keap_validation.sql
```

## Next
- Implement incremental pull jobs (`updated_at >= last_run`).
- Add upserts into `keap.*` tables.
- Enable nightly cron/systemd timer to run full validation after each export.
