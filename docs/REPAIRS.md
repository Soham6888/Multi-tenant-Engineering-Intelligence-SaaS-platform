# Local repair report

Date: 2026-09-24. AWS is explicitly deferred. No cloud infrastructure or paid AI service was provisioned.

## Repaired

- Organization collection requests now reach the optional Next.js catch-all proxy. Previously GET/POST /api/v1/organizations returned 404. Pagination query parameters are forwarded through the allowlist.
- Organization and membership lists now use bounded, scoped cursor pagination. The workspace UI supports loading further pages.
- Organization mutations acquire the organization lock before reading authorization state. Invitation acceptance rechecks issuer permissions and token validity under that lock. Concurrent owner changes preserve ownership and current permissions.
- Added configurable Redis per-user organization API limits, organization request-size limits, and no-store headers across API responses. Audit resource types now match membership and invitation actions.
- Fixed migration formatting that broke full backend CI lint, the stale real-browser assertion, and stale Next route types during typechecking. Clipboard failures now provide manual-copy guidance.
- Added reproducible PowerShell environment/check helpers and a disposable test-only API harness. Helpers use the portable project runtimes without changing global PATH.
- Expanded tests for the complete role matrix, cross-tenant mutations, concurrent ownership and invitation acceptance, issuer revocation, cursor isolation, rate limits and body limits. Browser tests exercise the actual collection proxy and paginated workspace lifecycle.

## Verification

- Backend: **89 tests passed**, PostgreSQL 17 with Fakeredis; Ruff, format and MyPy passed.
- Frontend: **28 desktop/mobile Playwright tests passed**, including two real HTTP/PostgreSQL flows; TypeScript, Prettier and production build passed.
- Test harness: Ruff lint and formatting passed.
- An earlier browser loading assertion timed out during concurrent backend tests. The complete rerun passed unchanged after backend checks completed. No claim of load-test coverage is made.
- One upstream Starlette/httpx deprecation warning remains; it does not fail tests.

Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1` from the project root after setting EIP_TEST_DATABASE_URL for PostgreSQL integration tests. The execution-policy override applies only to that process. Optional switches: -Build and -Browser. Real browser tests additionally require EIP_E2E_REAL_AUTH=1 and running services; see [testing guide](testing/testing.md). Without the database URL, integration tests are skipped with a warning.

## Environment and external prerequisites still unresolved

- Docker Desktop and WSL are absent. Installation/system virtualization setup and possibly a reboot are still needed before validating Docker Compose and container builds locally.
- No real Redis server is available. Fakeredis validates application behavior, not real service integration, wire protocol or production operations. A normal persistent backend still needs real Redis.
- Git origin is configured, but pushed state and remote GitHub Actions results were not verified. A Git remote does not connect the product to GitHub engineering data.
- Live GitHub authorization will need a user-owned GitHub application and callback/secret configuration when that phase is implemented.

## Product work still to implement

These are planned phases, not claimed repairs or unavailable dependencies:

- GitHub authorization, repository synchronization, webhook registration/signatures.
- Raw-event persistence, queue abstraction, independent workers, retries/backoff, idempotent processing and dead letters.
- Engineering domain records, aggregates, live dashboards, repository/PR/CI/deployment views and explainable health.
- Controlled analytics AI tools and provider abstraction. No fake assistant or paid provider is configured.
- Team/member management screens, email invitation delivery and verification, alerts, API keys, audit browsing and retention.
- Redis dashboard caching; OpenTelemetry, Prometheus, Grafana; load tests and further production hardening.
- Local object-storage abstraction when a concrete storage workload is introduced. Optional pre-commit tooling is not configured.

The dashboard remains explicitly labeled sample data. AWS adapters, Terraform and cloud deployment remain deferred at the user's request. Future dependencies should be introduced and tested with their owning feature, rather than installed without an implementation.
