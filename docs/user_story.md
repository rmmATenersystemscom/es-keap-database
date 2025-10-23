# User Story: Full-Fidelity Keap Export

## As
Ener Systems (Rene), the MSP owner with a Keap account.

## I want
A reliable, repeatable process to **export all Keap data** (contacts, companies, tags and tag-links, deals/pipelines/stages, tasks, notes, ecommerce orders/items/payments, files) into **PostgreSQL**, **preserving relationships** and **validating completeness**.

## So that
- We can migrate or back up our CRM data at any time.
- We can analyze/BI the data across tools.
- We can safely iterate on marketing/sales ops without lock-in.

## Acceptance Criteria
- ✅ Exporter connects via **OAuth2** (with refresh) or **API Key** (PAT/SAK) for small jobs.
- ✅ Paginates all endpoints until exhaustion, with **throttle-aware** backoff.
- ✅ Writes to Postgres with **idempotent upserts**; stores raw API payloads.
- ✅ Relationships enforced via foreign keys; **zero orphans** after load.
- ✅ **Validation pack** runs clean; snapshot report compares run-to-run row counts.
- ✅ A single `.env` controls credentials and DB settings.
- ✅ A manifest/log shows total objects retrieved per entity and any skipped pages/errors.
- ✅ Can run a **dry-run** (no writes) and **delta** mode (updated since timestamp).
- ✅ Produces CSV/Parquet exports on demand for external uses.
