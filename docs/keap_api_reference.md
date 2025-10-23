# Keap API Reference (Concise)

> This is a developer-facing summary to speed up implementation. For live docs, use Keap’s Developer Portal.

## Base URLs
- OAuth2 authorize: `https://accounts.infusionsoft.com/app/oauth/authorize`
- OAuth2 token: `https://api.infusionsoft.com/token`
- REST base: `https://api.infusionsoft.com/crm/rest` (append `/v1` or `/v2` per endpoint)
- Legacy XML-RPC base: `https://api.infusionsoft.com/crm/xmlrpc`

## Auth
- **OAuth2 Authorization Code** → `access_token` (Bearer) + `refresh_token` (rotate on refresh).
- **API Key** (PAT/SAK) → send `X-Keap-API-Key: <key>` (lower quotas; single app only).

## Throttles (typical)
- OAuth2: ~1500 req/min, 150k/day.
- PAT/SAK: ~240 req/min, 30k/day.
- Per-tenant throttle headers also apply. Read `x-keap-*` headers and backoff.

## Pagination
- Most endpoints use `limit` (up to ~1000) and `offset`; page until zero results.

## Common v1/v2 Objects & Endpoints (illustrative)
- **Contacts**
  - `GET /crm/rest/v1/contacts?limit=1000&offset=0`
  - `GET /crm/rest/v1/contacts/{id}`
  - `GET /crm/rest/v1/contacts/model` (fields + custom fields)
  - `GET /crm/rest/v1/contacts/{id}/tags`
  - `POST /crm/rest/v1/contacts/{id}/tags` (apply tagIds)
- **Companies**: `/crm/rest/v1/companies`
- **Tags**: `/crm/rest/v1/tags`
  - Contacts by Tag: `/crm/rest/v1/tags/{tagId}/contacts?limit=1000&offset=0`
- **Opportunities/Deals**: `/crm/rest/v1/opportunities` (v2 endpoints expanding)
  - Pipelines: `/crm/rest/v1/pipelines`
  - Stages: `/crm/rest/v1/opportunity/stage_pipeline/get` (variants exist in v1/v2)
- **Tasks**: `/crm/rest/v1/tasks`
- **Notes**: `/crm/rest/v1/notes`
- **Ecommerce** (availability varies by edition; v2 expanding): `/crm/rest/v1/orders`, `/payments`, `/products`, `/orders/{id}/items`
- **Files**: contact file box list/download endpoints exist in v1 (check per edition).

## Headers to watch
- `Authorization: Bearer <access_token>`
- `X-Keap-API-Key: <api_key>` (when using PAT/SAK)
- `x-keap-product-quota-available`, `x-keap-product-throttle-available`
- `x-keap-tenant-throttle-available`

## Error handling
- 401 → refresh token or re-auth.
- 429 → throttle; exponential backoff with jitter.
- 5xx → retry with backoff.

## Tips
- Export **reference tables first** (users, pipelines, stages, tags).
- Store **raw payloads** to `jsonb` for audit.
- Validate via SQL pack after each run.
