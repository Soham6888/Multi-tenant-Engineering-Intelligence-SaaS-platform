# Development plan and VS Code handoff

Updated: 2026-09-24. This is the execution plan, not a claim that planned features exist.

## 1. Start here

Open the **Engineering Intelligence Platform** folder as the VS Code workspace. Read, in order:

1. [Repository instructions](../AGENTS.md)
2. [Requirements](requirements/FRS.md), which summarize the authoritative user specification
3. [Implementation status](STATUS.md) and [repair report](REPAIRS.md)
4. This plan, then the relevant architecture, security and API documents

Use named milestones: the original specifications have different numeric phase labels. Do not restart foundation work or redesign the existing UI. AWS, Terraform and AWS adapters are deferred by explicit user instruction; retain their future architectural compatibility without provisioning them.

### Current baseline

| Area | Implemented | Remaining |
|---|---|---|
| Foundation | Monorepo, FastAPI, Next.js, PostgreSQL migrations, Redis client, Compose and CI definitions | Actual local Compose/real Redis validation; remote CI verification |
| Authentication | Registration/login/logout/me, password hashing, revocable sessions, CSRF/origin checks, rate limits | Email verification, recovery and further production hardening |
| Tenancy | Organizations, membership roles, invitations, cursor pagination, audit writes, concurrent permission protection | Team/member screens, email delivery, audit read API/UI |
| UI | Responsive shell and sample analytics; real account/workspace/invitation screens | Engineering data integration and remaining product screens |
| Engineering data | No live GitHub integration | GitHub, durable events, workers, normalization, aggregates |
| AI and operations | Structured request logs, readiness checks | AI tools/provider, complete telemetry, dashboards and load testing |

Last recorded checks: **89 backend tests and 28 browser tests passed**, plus Ruff, MyPy, TypeScript, formatting and Next production build. PostgreSQL was real; Redis was simulated. These are historical results to reproduce after changes, not permanent guarantees. One earlier concurrent browser run timed out; the full rerun passed unchanged. The test-only API was stopped after validation.

### What blocks what

- Missing Docker/WSL and real Redis block full local infrastructure verification. They do **not** block integration code, protocol design or deterministic tests.
- User-owned GitHub application credentials and authorization block live GitHub acceptance. They do **not** block an injectable GitHub client and fixture-based tests.
- A provider credential or an actually installed local model is needed for live LLM answers. Deterministic test doubles must remain test-only; an unconfigured UI must report that state.
- AWS and paid services are not prerequisites. Maximum total budget remains approximately INR 500.

## 2. Working agreements

For each small slice: understand requirements, document material decisions, implement, test, run locally, review and update status. Do not create speculative modules/tables or mark a milestone done with missing acceptance checks.

- Keep a modular monolith plus separate worker processes. Share domain code rather than duplicating business logic in workers.
- Enforce membership and permissions server-side for requests, jobs, cache keys, storage and AI tools. Carry tenant identity from trusted context and validate it again at execution boundaries.
- Use database uniqueness and tenant-safe foreign keys for invariants. Do not assume a GitHub actor is a platform User.
- Add dependencies only with their owning feature. Keep lockfiles, env examples, migrations and docs in the same change.
- Preserve the current visual direction; use [design references](design/README.md). Keep sample data visibly distinct until each panel actually reads live data.
- Ask only about material product/architecture decisions, credentials, privileged setup or paid/external actions. Continue independent work while those are pending.
- Never publish, deploy, provision cloud resources or send email to real people without authorization. Routine local coding and tests are already authorized.

## 3. Ordered milestones

### A. Reproduce the baseline and complete local services

Status: code exists; infrastructure verification pending. Requirements: QA-01, CACHE-01, SEC-01.

- [ ] Inspect git status and preserve existing uncommitted repairs before editing. Check the installed tools instead of assuming prior processes still run.
- [ ] Reproduce current checks with a disposable PostgreSQL database; record skips explicitly.
- [ ] When system setup permits, install/enable Docker Desktop with Linux containers and WSL as needed, then start the existing Compose stack.
- [ ] Validate Alembic migration completion, readiness, actual Redis limits/expiry and fail-closed behavior.
- [ ] Exercise registration, login, organization creation, invitation acceptance and logout against actual services.
- [ ] Verify CI execution when remote access is available; do not equate an existing workflow with a successful run.

Affected: scripts, Compose, env examples, CI and testing/deployment docs. Fix only failures observed. Exit: reproducible local startup and real-service checks recorded. If setup is unavailable, leave this gate pending and proceed with B's design and isolated implementation.

### B. GitHub connection and repository catalog

Requirements: GH-01, TEN-01, RBAC-01, SEC-01.

Progress 2026-09-24: ADR-005 authorization/binding choices accepted. Migration 0004 and the bounded, fixture-tested catalog client are implemented; PostgreSQL tenant constraints verified. Connection services, OAuth state/user proof, token minting, API/UI and live acceptance remain unfinished. The user separately authorized the modern workspace visual refresh delivered with this slice. See STATUS for exact test results and limitations.

**Decision gate before schema implementation:** the specification calls for OAuth but does not settle GitHub App installation versus OAuth App authorization. Prepare an ADR comparing organization access, repository selection, permissions, token lifecycle and webhook ownership; obtain the user's choice. A GitHub App is a candidate, not an approved replacement for the OAuth requirement. Consult current official GitHub documentation at implementation time.

- [ ] Specify installation/account-to-tenant binding, including whether one GitHub installation can belong to multiple platform organizations. Do not silently decide this data invariant.
- [ ] Define minimum provider permissions, revocation, secret encryption/reference strategy, callback validation and single-use state bound to the authenticated tenant administrator.
- [ ] Add Integration and Repository models/migration with properly scoped external-ID uniqueness and cross-tenant-safe relationships.
- [ ] Implement an injected GitHub HTTP client with bounded timeouts, pagination, rate-limit handling and explicit retryable/non-retryable failures.
- [ ] Implement admin connection/disconnection and callback routes; never expose provider tokens to the browser or logs.
- [ ] List accessible repositories, select tracked repositories, and show connection/sync state in the existing integrations UI.
- [ ] Define resumable initial-sync jobs; execute historical engineering sync through C/D, not in an HTTP callback.

Affected: backend integrations, models/schemas/repositories/services/API, migrations; frontend integrations/proxy; security/API/ERD docs and ADR.

Acceptance: wrong-role/cross-tenant connection attempts fail; callback replay/state mismatch fails; repository enumeration handles multiple pages; disconnect revokes local access and prevents queued jobs from using stale authorization. Fixture tests run without secrets. Live authorization is a separate credential-dependent gate.

### C. Durable webhook ingestion and asynchronous execution

Requirements: GH-02, EVT-01, EVT-02. Depends on B's tenant mapping and selected repositories.

**Design gate:** document the local durable queue implementation and transaction boundary in an ADR before implementation. An in-memory queue cannot provide cross-process durability. Prefer the simplest durable option using existing infrastructure; compare a PostgreSQL-backed queue with any proposed alternative. Define at-least-once delivery, not exactly-once processing.

- [ ] Persist raw WebhookEvent records with a justified delivery-ID uniqueness scope, payload size bounds and retention policy.
- [ ] Verify signatures against the exact request bytes before accepting a delivery. Resolve tenant/repository from trusted integration mappings, not a caller-supplied organization ID.
- [ ] Close the database-commit/enqueue failure gap with a transactional outbox or equivalent durable publication design, including crash recovery.
- [ ] Define a queue interface for enqueue, receive/lease, acknowledge and retry. Add the local adapter only; SQS remains deferred.
- [ ] Run ingestion separately from FastAPI, with bounded concurrency, leases, shutdown handling and job status.
- [ ] Classify errors; add capped exponential backoff/jitter, attempt limits, dead letters and an authorized replay operation.
- [ ] Support the required event names: push, pull_request, pull_request_review, issues, workflow_run, deployment, deployment_status. Document ignored actions and unsupported versions.

Acceptance: invalid signatures cause no persistence; duplicate deliveries have no duplicate effects; valid events are durably acknowledged without synchronous analytics; committed-but-unpublished work is recovered; a worker killed before acknowledgement does not lose work. Test expired leases, malformed jobs, queue outages, poison events and tenant mismatch. Record webhook latency under a documented local workload rather than claiming an arbitrary throughput.

### D. Normalize engineering data and complete initial synchronization

Requirements: GH-01/02, EVT-02, ANALYTICS-01. Depends on C.

- [ ] Introduce Commit, PullRequest, PullRequestReview, WorkflowRun, Deployment and justified Issue/actor records in small migrations.
- [ ] Define external identities, workflow attempt identity, deployment/status ordering, UTC timestamps and links to source records.
- [ ] Handle updates, duplicates, late/out-of-order events and missing parents; never overwrite newer state with older delivery state.
- [ ] Use the same normalization/services for initial sync and webhook updates. Checkpoint sync pages, handle provider limits and resume after restart.
- [ ] Define the historical import window with the user before committing to a potentially expensive full-history backfill.
- [ ] Reconcile missed updates and expose per-repository sync progress, failure and last successful refresh. Initial sync must converge while live webhooks arrive.

Acceptance: replay fixtures twice and compare final domain state; reverse event order; interrupt/restart sync; revoke integration mid-job; validate tenant isolation and GitHub actor separation. A selected test repository must converge to known source data in the live gate.

### E. Defined metrics, aggregate workers and query APIs

Requirements: ANALYTICS-01/02, CACHE-01, API-01. Depends on D.

Before coding calculations, write a metric dictionary covering event timestamps, windows, units, denominators, missing observations and eligibility rules. Resolve ambiguous definitions such as review duration and what counts as a deployment success with the user. Avoid treating missing data as zero or claiming DORA metrics without the required source data.

- [ ] Implement PR count/open/merged, cycle time, first-review latency and agreed review-duration semantics.
- [ ] Implement workflow count, success/failure rates and duration; distinguish cancelled/skipped runs and reruns.
- [ ] Implement deployment frequency, reliability and duration by environment; do not invent unavailable PR/CI associations.
- [ ] Implement commit/contributor/issue activity with documented identity and deduplication rules.
- [ ] Add daily aggregates with tenant/repository/date uniqueness and enough sums/counts to combine averages correctly. Define snapshot treatment for open PRs.
- [ ] Recompute affected periods idempotently after late data and provide a bounded backfill/rebuild path.
- [ ] Serve overview and repository/PR/CI/deployment endpoints with pagination, filters, range limits and freshness metadata.
- [ ] Add tenant-aware Redis cache keys, bounded TTL and aggregation-driven refresh/invalidation; authorization still happens on cache hits.

Acceptance: deterministic fixtures verify exact values, empty windows, UTC boundaries, late corrections, weighted averages, cancellations and cross-tenant cache isolation. Explain query plans for main dashboard queries. Dashboard requests read aggregates rather than scanning raw history.

### F. Connect the existing UI to real engineering data

Requirements: UI-01/02, HEALTH-01. Depends on E; integrate small usable screens as APIs become available.

- [ ] Implement active-organization context and permission-aware navigation backed by server checks.
- [ ] Wire overview, repository overview/PR/CI/deployment/activity tabs and collection pages to real APIs.
- [ ] Support 7/30/90-day and custom ranges plus meaningful repository/author/state filters. Preserve filters in the URL where useful.
- [ ] Show loading, empty, failed, stale, unauthorized and integration-disconnected states; explain sync freshness.
- [ ] Implement health as transparent workflow indicators. Any composite score needs an agreed formula and evidence; no individual rankings.
- [ ] Retain typography, spacing, accessible contrast, keyboard navigation and responsive behavior. Disable or explain unavailable actions.

Acceptance: desktop/mobile browser journeys use actual APIs for the principal flow; switching organizations cannot show the previous tenant's cached data; charts/tables/exports use matching periods and values. Remove sample labels only where data is truly live. Review against existing design captures instead of redesigning without reason.

### G. Evidence-backed AI assistant

Requirements: AI-01/02, CACHE-01, SEC-01. Depends on E and useful live views from F.

- [ ] Define provider and tool schemas. Implement bounded tool orchestration without arbitrary SQL or executable model-generated code.
- [ ] Build authorized repository/PR/CI/deployment metrics, recent events, period comparison and failure lookup tools.
- [ ] Inject tenant/user permissions from the authenticated backend; model arguments cannot choose another tenant or bypass role policy.
- [ ] Return structured values, query windows, freshness and record references. Separate retrieved facts from interpretation.
- [ ] Treat repository/issue/PR text as untrusted data; test prompt injection, tool misuse, missing evidence and unsupported causal claims.
- [ ] Add conversation storage if needed, authorization on every read, bounded input/history/tool calls, timeouts, rate limits and cost ceilings.
- [ ] Ship UI with evidence links and honest provider-unavailable states. Use test doubles only in tests; choose a live provider/local runtime only after budget and privacy review.

Acceptance: deterministic tool tests confirm the same values as analytics APIs; cross-tenant tools fail; no-evidence questions do not fabricate metrics; provider failure is recoverable. A real provider-backed answer remains a separately recorded live gate.

### H. Complete organization operations and notifications

Requirements: TEN-01, ALERT-01, KEY-01, AUDIT-01. Depends on relevant existing APIs/metrics; implement each item as its own slice.

- [ ] Finish member/role management and settings UI with last-owner safeguards and server permission feedback; implement team grouping only with a defined product use.
- [ ] Add paginated tenant-authorized audit browsing with safe metadata and documented retention.
- [ ] Add API key creation/revocation/rotation/last-use, one-time display, hashed storage, scope/role rules and rate limits; test revoked keys and wrong-tenant access.
- [ ] Add alerts with explicit time windows, thresholds, evaluation schedules, deduplication/cooldowns and evidence links.
- [ ] Add an email adapter and local capture transport for invitation/alert tests. Real delivery and verified-email onboarding need provider configuration and authorization.

Acceptance: forbidden mutations fail in UI and API; invitation/key secrets never reappear; repeated evaluations do not spam; notification failures retry safely. SMTP captures count as local tests, not proof of actual email delivery.

### I. Local production-readiness gate

Requirements: OPS-01, QA-01, SEC-01. Add request/job instrumentation in owning milestones; finish the operating experience here.

- [ ] Add OpenTelemetry and Prometheus instrumentation across API/database/queue/workers/cache/AI. Propagate correlation IDs and exclude secrets, payloads and high-cardinality labels.
- [ ] Add local Prometheus/Grafana Compose services and useful provisioned dashboards; define dependency readiness separately from liveness.
- [ ] Verify restart recovery, migration deployment order, database backup/restore and graceful worker shutdown.
- [ ] Add security/dependency checks to CI; verify the remote pipeline, container builds and the full acceptance journey.
- [ ] Load-test webhook acceptance, worker drain and aggregate reads; record machine, workload, latency, errors and bottlenecks.
- [ ] Review retention, credential rotation, session security, trusted proxy configuration and production HTTPS requirements.

Exit: reproduce the complete local journey with real PostgreSQL/Redis, observed workers and meaningful telemetry. Document unresolved live credentials separately. AWS remains deferred even when this milestone passes.

## 4. Immediate next development slices

| Order | Concrete result | Gate |
|---|---|---|
| 1 | Recheck baseline and actual Docker/Redis availability; update STATUS | No application redesign |
| 2 | GitHub authorization ADR and tenant-binding decision | Ask once about material choice; do independent setup/tests meanwhile |
| 3 | Integration/repository schema, security contract and provider client | Decision from slice 2; no credentials required for isolated tests |
| 4 | Connection/repository-selection API and UI | Fixture tests first; live credentials for live acceptance |
| 5 | Durable queue/publication ADR and webhook persistence | Tenant binding from B; no synchronous historical sync |
| 6 | Worker plus one complete pull-request event path | Crash/retry/idempotency tests before adding other event families |
| 7 | Expand normalization and resumable historical sync | All required event types and reconciliation |
| 8 | PR aggregate API and first live dashboard panel | Agreed metric definitions, exact-value tests |

Keep each slice reviewable; do not scaffold the entire roadmap at once. Complete and document each milestone before declaring the next one achieved. A blocked external check stays explicitly pending, not silently waived.

## 5. VS Code terminal workflow

From the workspace root, open a terminal using portable runtimes if global Node/uv are unavailable:

```powershell
powershell.exe -NoExit -NoProfile -ExecutionPolicy Bypass -Command ". ./scripts/enter-dev.ps1"
```

This changes PATH only in that terminal. Use committed lockfiles (`uv sync --frozen` in backend, `npm ci` in frontend) when restoring dependencies. Do not upgrade the stack merely to resume development.

After Docker becomes available, preserve an existing .env and start services:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose config --quiet
docker compose up --build --wait
Invoke-RestMethod http://localhost:8000/api/v1/health/ready
```

UI: http://localhost:3000. API docs: http://localhost:8000/docs. Stop with `docker compose down`; do not add `-v` unless intentionally deleting development data. Existing native processes may occupy ports 3000/8000/5432/6379; identify owners before stopping anything.

For native backend work, configure EIP_DATABASE_URL and EIP_REDIS_URL for actual services, then from backend run `uv run alembic upgrade head` followed by `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log`. Run `npm run dev` from frontend in a separate terminal. Liveness or a working sample dashboard is not proof that authentication dependencies are healthy.

Verification from the root:

```powershell
# Supply URLs for a disposable test database and a dedicated test Redis database.
# EIP_TEST_DATABASE_URL uses postgresql+asyncpg://...
# EIP_TEST_REDIS_URL uses redis://...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1 -Build
```

Without EIP_TEST_DATABASE_URL, database tests skip. Without EIP_TEST_REDIS_URL, tests use Fakeredis. These are not equivalent to full-service verification. Run browser tests after CPU-heavy backend checks; stop a dev server before building if its Next cache interferes. For real browser flows, start the frontend/API/database/Redis first, then from frontend:

```powershell
$env:EIP_E2E_REAL_AUTH = '1'
$env:EIP_EXTERNAL_WEB_SERVER = '1'
npm.cmd run test:e2e -- --workers=2
```

Use disposable environments: real browser tests create accounts/workspaces. The optional `scripts/e2e-api.py` harness is test-only and uses simulated Redis; see [testing guide](testing/testing.md). Never use it to hold real user data or claim the full stack is running.

## 6. Definition of done and handoff record

For every completed slice, record in STATUS:

- Requirement IDs and observable behavior delivered
- Files/modules, migrations and important decisions
- Commands actually run, pass/fail/skipped results, and real versus simulated dependencies
- Security checks, failure behavior and remaining risks
- How to run the result and the exact next unfinished slice

Update API/security/database/design docs when their contracts change and add ADRs for important choices. Do not reuse an existing ADR number. Inspect git diff and keep unrelated user edits intact. Commit/push only under the applicable user authorization; no automatic publication from this plan.

Final acceptance remains: register -> create organization -> invite/enforce roles -> connect GitHub -> select repository -> initial sync -> signed webhook -> durable job -> idempotent normalization -> aggregates -> live dashboard -> authorized AI tools -> evidence-backed answer. Cross-tenant denial, retries, Docker, real Redis, CI and observability are required alongside that journey.

## 7. Paste this into the next VS Code assistant session

> Continue development of Engineering Intelligence Platform in this workspace. Read AGENTS.md, README.md, docs/requirements/FRS.md, docs/STATUS.md and docs/DEVELOPMENT_PLAN.md first. Preserve existing changes. Foundation, authentication and initial tenancy are implemented; engineering dashboards are still sample data. Last recorded tests were 89 backend and 28 browser passes, using real PostgreSQL and simulated Redis. Inspect current state rather than assuming those services or results still hold.
>
> Follow the immediate slices in the development plan. Recheck the baseline, then prepare the GitHub authorization and tenant-binding decision before implementing its schema. Ask only for material decisions, credentials or privileged setup; continue independent local work while waiting. Do not block all coding on Docker or live credentials. Keep the existing UI design, modular monolith and worker architecture, tenant isolation and INR 500 budget. AWS is deferred. Implement small slices, add meaningful tests, run them and update documentation. Do not claim simulated integrations or sample data are live features.
