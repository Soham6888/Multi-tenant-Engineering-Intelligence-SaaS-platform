# Engineering Intelligence Platform

A local-first engineering intelligence product: GitHub activity → durable events → workers → aggregated analytics → evidence-backed AI investigation.

**Current milestone: local foundation, real account authentication and organization tenancy.** Registration, login, revocable browser sessions, tenant-scoped workspaces, role enforcement and single-use invitations use FastAPI/PostgreSQL. Authentication attempts are rate-limited with Redis. GitHub ingestion, live analytics and AI remain future phases. The main dashboard stays explicitly labeled sample data. See [implementation status](docs/STATUS.md).

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

Domain modules, worker directories, Alembic migrations, and Terraform will be created when their phases introduce real behavior. No placeholder infrastructure is claimed as implemented.

Start with [requirements](docs/requirements/FRS.md), [architecture](docs/architecture/system-architecture.md), [roadmap](docs/STATUS.md), and [testing](docs/testing/testing.md).

Implementation references: [Next.js installation](https://nextjs.org/docs/app/getting-started/installation), [FastAPI Docker guidance](https://fastapi.tiangolo.com/deployment/docker/).
