# ADR-001 — Local-first modular monolith

Status: accepted from the user's product specification.

## Context

A serious multi-tenant analytics product needs coherent boundaries, transactional data, asynchronous work and cloud readiness, while total spending is limited to approximately ₹500.

## Decision

Use a FastAPI modular monolith with independent workers introduced at the event-processing milestone. Develop with Next.js, PostgreSQL and Redis in Docker Compose. Add queue/storage/LLM adapters when their product workflows are built. Build named phases sequentially. The initial UI is explicitly labeled sample data.

## Reason

One deployable backend avoids unnecessary interservice coordination. Local containers remove the requirement for continuous AWS spending. Clear future worker boundaries allow workload isolation without fragmenting domain logic. UI fixtures permit early usability review without misleading users about backend completion.

## Alternatives

Microservices add deployment and transaction complexity before scale justifies them. Cloud-only development conflicts with budget. A synchronous webhook-to-analytics path would violate latency and failure-isolation requirements. An unlabeled simulated dashboard would misrepresent product status.

## Consequences

Positive: understandable architecture, lower cost, quick local iteration, honest implementation status. Negative: eventual consistency and worker operations arrive later; module boundaries require discipline. UI sample state will be replaced with authenticated API state. No business security is claimed until verified.
