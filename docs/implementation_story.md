# Implementation Story: Keap Exporter

## Architecture
- **Auth**: OAuth2 Authorization Code + Refresh (preferred for higher quotas). Optional **API Key** (PAT/SAK) for low-volume actions.
- **HTTP Client**: session with retries (HTTP 429/5xx), throttle-aware by reading `x-keap-*` headers.
- **Extractor**: generic `fetch_all(endpoint, params)` yields records across `limit/offset`.
- **Loader**: Postgres upserts into `keap.*` tables; `raw jsonb` column keeps exact payload.
- **Validator**: SQL pack for orphans, cross-object consistency, commerce reconciliation, duplicates, coverage.
- **Run Metadata**: `keap_meta.*` tables capture run logs, per-endpoint pages, and table snapshots/checksums.

## Entities (baseline)
- Reference: **users**, **pipelines**, **stages**, **tags**, **companies**.
- Core: **contacts** (→ companies, owners), **contact_tags** (many-to-many).
- Sales: **opportunities** (→ stages, pipelines), **tasks**, **notes**.
- E-comm: **products**, **orders**, **order_items**, **payments**.
- Files: contact file box items (download to filesystem + metadata table if desired).

## Data flow
1. **Bootstrap** reference tables.
2. **Load** companies and contacts.
3. **Load** junctions: contact↔tags.
4. **Load** deals/tasks/notes (+ owners).
5. **Load** ecommerce; reconcile via validation SQL.
6. **Files**: list + download to `/data/keap_files/<contact_id>/...` (optional).
7. **Snapshot** counts/checksums; run validations; alert on drift.

## Operational concerns
- **Secrets**: `.env` only; no secrets in code.
- **Backoff**: exponential, jitter; obey header budgets.
- **Idempotency**: `INSERT ... ON CONFLICT DO UPDATE` keyed by Keap IDs.
- **Observability**: structured logs with per-endpoint timing, pages, throttle hits.
- **Resilience**: resume from last successful entity/page on restart.
- **Safety**: dry-run mode prints plan and first page only.

## Deliverables
- Python package `keap_export` with `auth`, `client`, `db` helpers.
- CLI scripts for connection test and future `sync_*` commands.
- Docs + SQL packs + Cursor master prompt.
