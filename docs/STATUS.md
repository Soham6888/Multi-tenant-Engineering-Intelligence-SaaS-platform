# Implementation status

Recorded: 2026-09-24. Current milestone: **Foundation, Authentication and Organization Tenancy implemented**. Full Docker Compose startup and production Redis wire-protocol behavior still need verification on Docker Desktop/Redis.

## Delivered

- Responsive sample analytics dashboard, local fonts, repository filters/drill-down, PR states, CSV export, desktop/mobile preview captures.
- Real registration/login/logout/current-user API and sign-in, account and registration screens, connected by a same-origin Next.js auth proxy.
- Tenant-scoped workspaces with collision-safe slugs, membership listing and server-enforced OWNER/ADMIN/MANAGER/DEVELOPER/VIEWER roles.
- Member removal/role mutation controls in the API, including administrator limits and transaction-serialized protection against removing/demoting the last owner.
- Seven-day, single-use email-matched invitations; only token digests are stored, re-issuing invalidates the previous token, and invite acceptance joins the authenticated account.
- Authenticated workspace list/create UI with isolated sample analytics disclosure, and an allowlisted same-origin organization API proxy.
- OWNER/ADMIN invitation creation UI displays the one-time token for private delivery; it makes clear no email is sent.
- Organization-scoped security audit records, plus additive Alembic migrations for organizations, memberships, invitations and tenant-linked audit records.
- Argon2id password hashing, generic credential failures, normalized unique emails, hashed opaque database sessions, fixed expiry, login session rotation and immediate logout revocation.
- Explicit browser Origin and request-header checks, session-bound CSRF value, authentication request-size cap, no-store auth responses, bounded Argon2 concurrency.
- Redis authentication IP/account request limits with expiry and fail-closed behavior. Audit reads are not implemented yet.
- Alembic user/session/audit tables with uniqueness, foreign keys and indexes. Compose runs a one-shot migration before the API starts.
- Independent system-independent unit and browser checks, PostgreSQL schema-isolated integration tests, CI for Postgres/Redis and a gated real-browser auth journey.
- Updated authentication ADR, API/security/deployment/testing docs and scoped test-only loopback Fakeredis server.

## Verification performed locally

| Check | Result |
|---|---|
| Ruff lint and formatting | Passed |
| MyPy strict on application modules | Passed |
| Ruff check and formatter | Passed |
| Pytest with PostgreSQL 17 | 29 passed (Fakeredis used for auth limits); one upstream Starlette/httpx deprecation warning |
| PostgreSQL migrations through tenant audit migration | Passed in schema-isolated tests |
| PostgreSQL auth and tenancy integration | Passed: auth lifecycle, tenant isolation, unique slug collision, last-owner protection, invitation hashing/replacement/matching/single use and role enforcement |
| Authentication browser screens, mocked routes, desktop/mobile | 8 passed across desktop/mobile |
| Real browser signup, cookie, reload, logout and protected-account redirect | 1 passed against FastAPI, PostgreSQL 17 and loopback test-only Fakeredis |
| Dashboard desktop/mobile browser suite | 10 passed in the Foundation milestone |
| Next.js production build and TypeScript | Passed with workspace, invitation UI and organization proxy |
| Prettier | Passed |
| Playwright desktop/mobile | 22 passed, 2 gated real-API runs skipped; workspace create, invite issue and invite acceptance flows included |
| Compose YAML | Parsed in Foundation; Docker Compose rendering/runtime not available here |
| Docker service stack | Not run; Docker Desktop absent |
| Production Redis service | Not installed; test suite used Fakeredis and the local browser test used its protocol simulator |
| Remote GitHub Actions | Not run; no remote repository is configured |

Authentication API and test processes were run locally. The full stack currently has no real Redis server on this machine. A test-only Redis simulator is not a production dependency.

## Deliberate limits

The overview dashboard still displays labeled sample data and is not connected to the user's workspaces. GitHub, event workers/queue, normalized engineering analytics, meaningful dashboard cache, email alerts, API-key management, audit-log listing, AI, OTel/Prometheus/Grafana and AWS/Terraform are not yet implemented. Invitation delivery/verified email, password reset, MFA and session-management UI remain future work. The authentication UI confirms HTTPS will be required for secure production cookies, but public deployment is not configured.

The browser proxy shares one server network IP. Per-account rate limiting still works; deploy IP limits only behind an explicitly trusted proxy policy. Do not trust arbitrary forwarded IP headers.

All repository/PR/deployment signals remain demo fixtures. No paid AI call or cloud resource was created.

## Next milestone

Next milestone: GitHub app connection and repository catalog/synchronization design. Full Docker Compose/Redis verification remains environment-dependent. Registering a user alone does not grant tenant access; workspace APIs require active membership on every request.
