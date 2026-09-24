# Engineering Intelligence Platform

Read README.md, docs/requirements/FRS.md, and docs/STATUS.md before changing code.
The user's master project specification is the source of truth. Never silently change it.

- Local-first modular monolith with independent workers; maximum total cloud budget ₹500.
- Implement one validated phase at a time. Foundation is current; authentication is next.
- Backend: Python/FastAPI/Pydantic/SQLAlchemy/Alembic/PostgreSQL. Frontend: Next.js/TypeScript.
- Redis needs an actual caching/rate-limiting responsibility when business endpoints arrive.
- Queue, storage, and LLM integrations use adapters when introduced; no speculative frameworks.
- Organization authorization must be enforced on the server for every tenant-owned operation.
- Never treat frontend fixtures, profile labels, or navigation as authentication or live analytics.
- Keep demo data explicitly labeled. Never generate fake AI responses or claim untested features.
- Add meaningful tests, run checks, document implementation status and verification limits.
- Do not introduce paid resources, publish, or perform major architecture changes without discussion.
- Routine reversible work inside this project is authorized; do not ask for repeated confirmations.
- No secrets in source, logs, frontend bundles, or commits. Do not include .tools or dependency folders.
- UI: restrained B2B design, legible information hierarchy, responsive layouts, keyboard access.

Checks: backend `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy app`,
`uv run pytest`; frontend `npm run typecheck`, `npm run build`, `npm run test:e2e`.
Full stack: `docker compose up --build --wait`, then GET /api/v1/health/ready.
