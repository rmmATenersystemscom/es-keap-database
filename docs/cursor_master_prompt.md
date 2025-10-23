You are assisting on the **Keap Exporter (Python)** project.

## Context
- Goal: Export all Keap data to PostgreSQL, **preserving relationships**, and run **validation** after each run.
- Stack: Python 3.11+, requests/tenacity, psycopg2, dotenv, Postgres.
- Artifacts available in workspace: 
  - `/docs/user_story.md`, `/docs/implementation_story.md`, `/docs/project_layout.md`,
  - `/docs/keap_api_reference.md`,
  - `/sql/schema.sql`, `/sql/keap_validation.sql`, `/sql/keap_etl_support.sql`,
  - `/src/keap_export/*` helpers and `/src/scripts/sample_connect.py`.

## Directives
1) Read ALL docs under `/docs` and `/sql`. Follow architecture and naming.
2) Implement incremental sync modules: `sync_contacts`, `sync_companies`, `sync_tags`, `sync_contact_tags`, `sync_opportunities`, `sync_tasks`, `sync_notes`, `sync_products`, `sync_orders`, `sync_order_items`, `sync_payments`.
3) Each sync must:
   - Use `client.fetch_all(path, params)` and respect throttle headers.
   - Upsert to Postgres using `db.upsert(table, pk, row_dict)`.
   - Persist raw payload in `raw` column.
   - Record per-entity counts in `keap_meta.source_counts`.
4) Add CLI commands under `/src/scripts/` for each sync; accept `--since` (ISO time) and `--dry-run` flags.
5) After a full run, execute SQL in `/sql/keap_validation.sql` and print a summary; fail pipeline if non-zero orphans.
6) Log JSON lines with entity, page, count, duration, remaining throttles.
7) Keep code idempotent and restartable.

## Style & Standards
- Pythonic, typed where helpful; short functions.
- Robust retries (429/5xx), **never** busy-loop; use exponential backoff + jitter.
- Secure: load secrets from `.env` only; never print tokens.
- Unit-test critical helpers (token refresh, pagination math).

## Deliverables
- Working `sync_*.py` modules
- CLI wrappers
- Tests for client/auth/backoff

Now propose a task list and start with `sync_contacts` and `sync_tags`.


Additional doc to read: `/docs/keap_functionality_user_stories.md` (Ener Systems tailoring).