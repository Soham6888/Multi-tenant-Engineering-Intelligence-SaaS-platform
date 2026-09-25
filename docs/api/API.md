# API contract

Current implemented routes:

| Method | Route | Contract |
|---|---|---|
| GET | /api/v1/health/live | 200 `{ "status": "ok" }`; no external dependencies |
| GET | /api/v1/health/ready | 200 `{ "status": "ready" }` only when PostgreSQL and Redis respond; otherwise 503 |
| POST | /api/v1/auth/register | 201 safe identity and CSRF value; sets an HttpOnly session cookie |
| POST | /api/v1/auth/login | 200 safe identity and CSRF value; rotates existing session |
| POST | /api/v1/auth/logout | 204; validates Origin and session-bound CSRF before revoking session |
| GET | /api/v1/auth/me | 200 safe identity and CSRF value for a valid session; otherwise 401 |

| Method | Route | Access and behavior |
|---|---|---|
| GET | /api/v1/organizations | List only the signed-in user's workspaces and membership roles |
| POST | /api/v1/organizations | Create a workspace; creator becomes OWNER; duplicate slugs receive a suffix |
| GET | /api/v1/organizations/{id} | Get one workspace only when the caller is a member |
| GET | /api/v1/organizations/{id}/members | List workspace members; membership required |
| PATCH | /api/v1/organizations/{id}/members/{user_id} | OWNER/ADMIN role management, with role limits and last-owner guard |
| DELETE | /api/v1/organizations/{id}/members/{user_id} | OWNER/ADMIN member removal, with role limits and last-owner guard |
| POST | /api/v1/organizations/{id}/invitations | Issue/replace a seven-day invitation; returns its raw token once |
| POST | /api/v1/organizations/invitations/accept | Authenticated matching-email account accepts a token exactly once |
| GET | /docs | Generated OpenAPI UI |

Every response carries a server-generated X-Request-ID. Standard errors:

```json
{"error":{"code":"DEPENDENCY_UNAVAILABLE","message":"A required dependency is unavailable","request_id":"req_<uuid>"}}
```

Unknown routes use RESOURCE_NOT_FOUND, unsupported methods METHOD_NOT_ALLOWED, validation failures VALIDATION_ERROR, unexpected failures INTERNAL_ERROR. Input values and internal exception messages are not returned.

The same-origin Next.js proxy exposes only the documented auth and organization routes. Mutations require an exact configured Origin and `X-EIP-Request: 1`; logout also needs `X-CSRF-Token` from login/register/me. Local cookies are HttpOnly/SameSite=Lax; production cookies are Secure with the `__Host-` prefix. Auth responses are no-store. Registration requires a 15–128 character password and duplicate registration returns a generic conflict. Login errors do not reveal whether an email exists. Organization access requires membership in every handler; nonmembers receive a generic 404.

Upcoming contract families: repositories and repository metrics; analytics/overview, deployments, pull-requests, ci; integrations/github; webhooks/github; ai/chat; alerts and audit-log listing. Audit writes are present; no audit read route exists yet. Invitation delivery is out of band; this API does not claim to send email or verify email ownership. See FRS for behavior. No stub route implies these exist.

Collection contract uses `data` plus `pagination: {has_more, next_cursor}`. Cursor validation, limits, ordering and tenant scope belong to each implementation. No unauthenticated business endpoint should be introduced ahead of auth and tenancy.

## Collection contract and abuse controls

`GET /api/v1/organizations` and `GET /api/v1/organizations/{id}/members` now accept `limit` (default 25, maximum 100) and `cursor`. Both return:

```json
{"data": [], "pagination": {"has_more": false, "next_cursor": null}}
```

Ordering is stable by UUID, not name or join time. Cursors are scoped to the caller and collection, and membership is still authorized separately on every request. Cursors are traversal positions, never authorization credentials. The Next.js organization proxy forwards these pagination parameters.

All organization requests have a configurable per-user Redis budget (`EIP_API_USER_LIMIT`, default 120; `EIP_API_WINDOW_SECONDS`, default 60). Redis failure denies these requests with 503. Rate-limit errors include Retry-After. Current account/organization POST and PATCH bodies are bounded at 16 KiB before parsing, and API responses carry Cache-Control: no-store, including errors and invitation tokens.
