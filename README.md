# Engineering Intelligence Platform

A local-first engineering intelligence product: GitHub activity → durable events → workers → aggregated analytics → evidence-backed AI investigation.

**Current milestone: local foundation, real account authentication and organization tenancy.** Registration, login, revocable browser sessions, tenant-scoped workspaces, role enforcement and single-use invitations use FastAPI/PostgreSQL. Authentication attempts are rate-limited with Redis. GitHub ingestion, live analytics and AI remain future phases. The main dashboard stays explicitly labeled sample data. See [implementation status](docs/STATUS.md).

The next GitHub slice now includes tenant-safe installation/repository tables and a bounded, tested catalog client. OAuth connection and live ingestion are not available yet. The refreshed workspace includes a responsive sample review queue with repository drill-down; see [current UI captures](docs/design/README.md).

## Run the local stack

Install Docker Desktop with Linux container support and Docker Compose. From this folder:

```powershell
Copy-Item .env.example .env
docker compose up --build --wait
```

- Interface: http://localhost:3000
- API documentation: http://localhost:8000/docs
- Liveness: http://localhost:8000/api/v1/health/live
- PostgreSQL/Redis readiness: http://localhost:8000/api/v1/health/ready
- Register: http://localhost:3000/register
- Sign in: http://localhost:3000/login

Stop with `docker compose down`. PostgreSQL data is retained in a named volume. No cloud services are provisioned. Database credentials in `.env.example` are local development placeholders; all published ports bind to loopback.

## Run without containers

Prerequisites: Node.js 22 and uv (Python 3.12 is managed by uv).

```powershell
cd frontend
npm ci
npm run dev
```

In another terminal:

```powershell
cd backend
uv sync --frozen
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

The dashboard preview and API liveness work without databases. Authentication and readiness require PostgreSQL/Redis and a successful migration; readiness returns 503 before dependencies respond.

This machine's initial setup also includes ignored portable runtimes under `.tools`. Run `./scripts/dev.ps1` to start the UI with that Node installation. Use a second terminal with `./scripts/api.ps1` for the API. These scripts fall back to installed runtimes on other machines.

## What's in this milestone

- Responsive Next.js shell with overview, repository drill-down, PR filters, CI and deployment previews.
- Deterministic sample data; date ranges recalculate counts and charts, repository filtering, CSV export.
- Honest empty states for upcoming modules and a non-connected AI assistant preview.
- FastAPI configuration, OpenAPI, request IDs, safe structured request logs, standardized errors.
- Dependency readiness checks with a bounded timeout; SQLAlchemy and Redis lifecycle management.
- Argon2id account registration/login, hashed and revocable sessions, auth attempt limits and audit writes.
- Tenant-scoped workspaces, membership roles, invite acceptance and server-side ownership checks.
- Organization-scoped audit records and tenant isolation integration tests against PostgreSQL.
- Alembic auth migration and PostgreSQL-backed auth lifecycle tests.
- Docker builds, local Compose topology, locked dependencies, tests, and a CI workflow.

The dashboard uses sample state and does not fetch engineering tenant data. Accounts are real but do not create an organization or grant access to the demo. Fixed repository cycle/review averages are illustrative, not historical calculations; the date filter applies to generated daily series.

## Validation

```powershell
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
```

```powershell
cd frontend
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e
```

The CI workflow also builds containers and checks readiness with real PostgreSQL and Redis. A committed workflow is not evidence that a remote CI run has passed; see [status](docs/STATUS.md) for recorded local results.

## Project map

```text
backend/app/       API bootstrap and core configuration
backend/tests/     Foundation API tests
frontend/app/      Next.js application and design system
frontend/components/  Workspace and accessible SVG charts
frontend/lib/      Explicit demo fixtures
frontend/tests/    Browser journeys for desktop and mobile
docs/             Requirements, architecture, decisions, testing and security
scripts/          Local development entry points
.github/workflows/ Foundation verification workflow
```

Auth and organization modules and Alembic migrations are implemented. Workers and integration modules arrive with their owning phases. AWS and Terraform are deferred at the user's request.

Start with [requirements](docs/requirements/FRS.md), [architecture](docs/architecture/system-architecture.md), [development plan and VS Code handoff](docs/DEVELOPMENT_PLAN.md), and [testing](docs/testing/testing.md).

Implementation references: [Next.js installation](https://nextjs.org/docs/app/getting-started/installation), [FastAPI Docker guidance](https://fastapi.tiangolo.com/deployment/docker/).

## Local repair and verification tools

The organization proxy now covers both the collection and child routes. Organization and member collections return `data` and `pagination` with a bounded `limit` (1?100) and an optional scoped cursor. The workspace screen supports loading additional pages.

For the portable tools on this Windows machine, open a project terminal with:

```powershell
powershell.exe -NoExit -NoProfile -ExecutionPolicy Bypass -Command ". ./scripts/enter-dev.ps1"
```

This changes PATH only in that terminal, not system settings. To run full backend checks (including migrations), frontend type generation and formatting:

```powershell
# Set EIP_TEST_DATABASE_URL to a disposable PostgreSQL test database first.
# Set EIP_TEST_REDIS_URL for real Redis; otherwise backend tests use Fakeredis.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
```

Use `-Build` for the production frontend build and `-Browser` for browser tests. A missing test database is reported explicitly; integration tests then skip. The execution-policy flag applies only to that invocation; it does not change the machine policy.

Docker Desktop and WSL are not installed on this machine. The full Compose stack remains unverified locally. No AWS installation or resource is required. See [the repair record](docs/REPAIRS.md) for current evidence and remaining work.
