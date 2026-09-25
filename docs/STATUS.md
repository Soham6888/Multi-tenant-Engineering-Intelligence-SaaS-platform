# Implementation status

Recorded: 2026-09-24. Current milestone: **Foundation, Authentication and Organization Tenancy implemented**. Full Docker Compose startup and production Redis wire-protocol behavior still need verification on Docker Desktop/Redis.

## Delivered

- Responsive sample analytics dashboard, local fonts, repository filters/drill-down, PR states, CSV export, desktop/mobile preview captures.
- Real registration/login/logout/current-user API and sign-in, account and registration screens, connected by a same-origin Next.js auth proxy.
- Tenant-scoped workspaces with collision-safe slugs, cursor-paginated workspace and membership listing and server-enforced OWNER/ADMIN/MANAGER/DEVELOPER/VIEWER roles.
- Member removal/role mutation controls in the API, including administrator limits and transaction-serialized protection against removing/demoting the last owner.
- Seven-day, single-use email-matched invitations; only token digests are stored, re-issuing invalidates the previous token, and invite acceptance joins the authenticated account.
- Authenticated workspace list/create UI with isolated sample analytics disclosure, and an allowlisted same-origin organization API proxy.
- OWNER/ADMIN invitation creation UI displays the one-time token for private delivery; it makes clear no email is sent.
- Organization-scoped security audit records, plus additive Alembic migrations for organizations, memberships, invitations and tenant-linked audit records.
- Argon2id password hashing, generic credential failures, normalized unique emails, hashed opaque database sessions, fixed expiry, login session rotation and immediate logout revocation.
- Explicit browser Origin and request-header checks, session-bound CSRF value, authentication and organization request-size caps, no-store API responses, bounded Argon2 concurrency.
- Redis authentication IP/account and organization per-user request limits with expiry and fail-closed behavior. Audit reads are not implemented yet.
- Alembic user/session/audit tables with uniqueness, foreign keys and indexes. Compose runs a one-shot migration before the API starts.
- Independent system-independent unit and browser checks, PostgreSQL schema-isolated integration tests, CI for Postgres/Redis and a gated real-browser auth journey.
- Updated authentication ADR, API/security/deployment/testing docs and scoped test-only loopback Fakeredis server.

## Verification performed locally

Repair validation on 2026-09-24:

| Check | Result |
|---|---|
| Full backend Ruff lint/format, including migrations | Passed |
| MyPy application modules | Passed |
| Pytest with PostgreSQL 17 | 89 passed; Fakeredis; one upstream Starlette/httpx deprecation warning |
| Migrations | Applied in isolated PostgreSQL test schemas |
| Next.js TypeScript and Prettier | Passed |
| Next.js production build | Passed, including optional organization collection route |
| Playwright desktop/mobile | 28 passed, no skips; includes actual proxy and HTTP/PostgreSQL registration, workspace creation, pagination and logout |
| Test harness lint/format | Passed |
| Docker Compose runtime | Not verified: Docker Desktop and WSL are absent |
| Real Redis | Not installed; simulated with Fakeredis during local tests |
| Remote GitHub Actions | Not verified; origin is configured, which does not establish workflow success |

One earlier desktop real-API test timed out on its loading screen while the backend suite ran concurrently. The complete browser suite passed when rerun after backend checks, without changing its timeout. This is a local timing limitation, not evidence of production performance.

The test-only API uses an isolated disposable PostgreSQL schema and simulated Redis; it is stopped after verification. It is not an operational application backend. See [repair report](REPAIRS.md) for completed fixes and remaining work.

## Deliberate limits

The overview dashboard still displays labeled sample data and is not connected to the user's workspaces. GitHub, event workers/queue, normalized engineering analytics, meaningful dashboard cache, email alerts, API-key management, audit-log listing, AI, OTel/Prometheus/Grafana and AWS/Terraform are not yet implemented. Invitation delivery/verified email, password reset, MFA and session-management UI remain future work. The authentication UI confirms HTTPS will be required for secure production cookies, but public deployment is not configured.

The browser proxy shares one server network IP. Per-account rate limiting still works; deploy IP limits only behind an explicitly trusted proxy policy. Do not trust arbitrary forwarded IP headers.

All repository/PR/deployment signals remain demo fixtures. No paid AI call or cloud resource was created.

## Next milestone

Next milestone: GitHub OAuth connection/disconnection services and tenant-authorized repository catalog/selection API, then workspace integration UI. The catalog schema/client slice is implemented below. Full Docker Compose/Redis verification remains environment-dependent. Registering a user alone does not grant tenant access; workspace APIs require active membership on every request.

## GitHub catalog foundation and workspace refresh (2026-09-24)

Requirements advanced: GH-01, TEN-01, SEC-01, UI-01/02. This is a validated schema/client slice, not completion of GitHub authorization or live analytics.

- Added migration `0004_github_catalog`, Integration and Repository models, exclusive active/suspended installation binding, immutable external IDs and composite tenant-safe foreign keys. No credentials are stored. See [database contract](database/schema.md).
- Added an injected GitHub catalog HTTP adapter with typed summaries, fixed host, no redirects, bounded pages/body/timeouts, one transient retry and rate-limit scheduling hints. Moved the existing httpx dependency into runtime dependencies and updated the lockfile without a stack upgrade. See [client contract](api/github-client.md).
- Refreshed the dashboard with a slate/mint palette, stronger typography, rounded panels and a responsive sample review queue. Queue entries navigate to the matching repository and awaiting-review filter. Updated desktop/mobile captures in [design references](design/README.md). Engineering data remains explicitly sample-only.
- Full checks: Ruff lint/format, MyPy, TypeScript, Prettier and production build passed. Full backend suite: **102 passed** with real PostgreSQL 17 and Fakeredis. Following a rate-hint hardening change, the complete GitHub client suite passed **14 tests**, including two additional cases. The full suite was not repeated after that isolated change.
- Browser suite: **28 passed, 2 gated real-API tests skipped**. Then both real registration/workspace/pagination/logout journeys and both review-queue journeys passed in a targeted **4-test** run. Together these exercise all 30 browser cases; this is not a single 30-test run.
- An initial migration attempt exposed a branching revision; fixed by placing the new migration after `0003_audit_tenant`. A first real-browser run timed out during concurrent route compilation/screenshots; rerun passed unchanged after warmup. Pytest reported the existing upstream deprecation and unwritable cache warnings. No performance claim is made.
- Tests used a new disposable loopback PostgreSQL cluster on port 55434 with role `eip_test`, leaving the old cluster untouched. The real-API browser harness still uses simulated Redis and disposable test accounts. Docker/real Redis, remote CI and live GitHub credentials remain unverified.

No OAuth callback, provider administration proof, token minting, repository-selection API, webhook endpoint or worker has been delivered in this slice. No cloud resources, paid services, commits or publication were performed.

The frontend, test API and disposable PostgreSQL instance were stopped after verification.

## Resume verification and GitHub proposal (2026-09-24)

- Prepared [ADR-005](decisions/ADR-005-github-authorization.md): the user approved GitHub App with OAuth user verification and exclusive installation-to-organization binding. The design decision gate is satisfied; no integration schema or application behavior changed.
- Ran `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1 -Build -Browser`. The first attempt was blocked by uv cache access; the approved rerun passed Ruff lint/format, MyPy, frontend typecheck/Prettier and production build.
- This rerun produced **21 backend passes and 68 skips**, because `EIP_TEST_DATABASE_URL` was unset; **26 browser passes and 2 skips**, because the real API journey was not enabled. These results do not reproduce the earlier full PostgreSQL/browser verification. Pytest also reported an unwritable cache warning and the existing upstream deprecation warning.
- Portable PostgreSQL on port 55432 was initially stopped. An approved start succeeded after a sandboxed Windows token error, but tested local role names did not exist; no configured test connection was established. No database roles or data were changed. The server was stopped after the probe.
- Docker and redis-server commands were unavailable; `wsl --status` reported WSL is not installed. Compose/readiness, real Redis and remote CI remain unverified.
- Next: implement the integration/catalog schema and tested provider client under ADR-005; restore a valid disposable PostgreSQL test connection and reproduce the full tests. Connection routes/UI and live credentials follow in their own slices.
