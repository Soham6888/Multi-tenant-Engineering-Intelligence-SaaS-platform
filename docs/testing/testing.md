# Testing strategy

Foundation tests exercise liveness without dependencies, request ID integrity, standardized 404 errors, readiness checks and safe failure responses. Auth tests exercise Argon2id, invalid inputs, normalized identities, Redis atomic limits/expiry and fail-closed behavior, origin/CSRF and request-size guards. Database tests create a disposable PostgreSQL schema per test, apply all migrations, then drop only their own schema. They cover registration, duplicate races, session rotation/expiry/logout, audit persistence, equivalent login failures, organization isolation, role restrictions, last-owner serialization, slug conflicts and invitation replacement/expiry/matching/single use. Redis defaults to a per-test Fakeredis instance; set `EIP_TEST_REDIS_URL` to run against Redis.

Playwright runs desktop/mobile journeys: sample disclosure, date-range changes, viewport overflow, repository filtering/drill-down, PR states, integration preview, CSV export, login/register/account/sign-out, request failures and password visibility. The gated real-browser auth test runs the whole browser journey when `EIP_E2E_REAL_AUTH=1` and services are available.

CI is configured for backend Ruff/format/MyPy/Pytest; frontend typecheck/build/browser journeys; and Docker Compose build/start/readiness. Container readiness is an infrastructure smoke check, not full database integration coverage. Remote workflow execution status must not be inferred from a configuration file.

PostgreSQL 17 migrations and tenant integration tests pass locally using a portable test server. Rate-limit behavior was tested with Fakeredis. Real Redis wire-protocol and Compose verification are pending; this machine has neither Docker nor a Redis server. Remaining gates include signed GitHub payloads; delivery ordering/retries; analytics definitions and AI authorization. Final E2E follows the FRS acceptance journey.

See docs/STATUS.md for what was actually executed on this machine and unresolved prerequisites.

## Tests added after the dependency audit

- The full `ruff check .` and formatter include migrations; checking only `app tests` is insufficient.
- Tenant regressions cover the five-by-five actor/target role matrix for PATCH and DELETE, cross-tenant writes, administrator promotion restrictions, competing owner updates, duplicate invitation acceptance, invalid/expired/replaced invitations, revoked issuers, pagination scope/limits, request-size caps and Redis failure.
- Proxy browser tests call the actual Next server through Playwright's request client instead of page-route mocks.
- The gated real-registration browser test creates two workspaces, traverses paginated results through the actual Next/FastAPI proxy, reloads the cookie session, then logs out.
- `npm run typecheck` regenerates Next route types before tsc, avoiding stale route imports after a rename.

For local end-to-end tests without Docker, `scripts/e2e-api.py` is a test-only loopback server: it migrates a fresh PostgreSQL schema, uses Fakeredis and drops its schema on graceful shutdown. From backend, set EIP_TEST_DATABASE_URL and PYTHONPATH to the backend directory, then run the script with the project Python interpreter. Never use this harness for real accounts. Set EIP_E2E_REAL_AUTH=1 and EIP_EXTERNAL_WEB_SERVER=1 for browser tests against it. This validates the real HTTP/proxy/database flow but not a real Redis server; Docker CI remains that gate.
