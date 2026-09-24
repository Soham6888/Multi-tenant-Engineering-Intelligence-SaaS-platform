# Functional requirements — baseline 1.0

This document consolidates the user's Master AI Development Prompt and Master Project Documentation. Those supplied specifications remain authoritative; this summary does not relax them. Both use the same phase sequence with different numbering. We use named milestones, starting with Foundation, to avoid ambiguity.

## Product and constraints

Multi-tenant B2B engineering intelligence SaaS for owners, administrators, engineering managers, leads, developers, and viewers. Explain what happened, what changed, where delivery bottlenecks exist, and what to investigate. Evidence supports interpretation; correlations must not be presented as proven causes. Never rate employees. Every technology must serve a product need.

Local-first with a maximum ₹500 budget. Docker runs most development. AWS is an optional future target, never a prerequisite for routine work. Architecture is a modular monolith plus independently scalable background workers. Do not add Kubernetes, Kafka, microservices, CQRS, event sourcing, service meshes, vector databases, or additional cloud providers without a demonstrated need and discussion.

## Requirements register

| ID | Requirement |
|---|---|
| AUTH-01 | Registration, login, logout, current user, secure password hashing, revocable sessions/tokens, protected endpoints; compatible with future OAuth/SSO without building those prematurely. |
| TEN-01 | Organizations, membership, invitations, teams, server-enforced tenant isolation on all owned entities and analytics/tool calls. |
| RBAC-01 | OWNER, ADMIN, MANAGER, DEVELOPER, VIEWER; owner organization control, admin members/integrations/settings, manager analytics/health/AI, developer engineering information, viewer read-only. Initial implemented/planned permissions are recorded in [the RBAC matrix](../security/rbac.md). |
| GH-01 | Authorize GitHub, enumerate accessible repositories, select repositories, initial synchronization, register webhooks, disconnect integration. Use GitHub IDs, not repository names, as identity. |
| GH-02 | Support push, pull_request, pull_request_review, issues, workflow_run, deployment, deployment_status. |
| EVT-01 | POST /api/v1/webhooks/github verifies signatures, checks delivery ID, durably persists raw events, schedules asynchronous work, and acknowledges quickly. No expensive synchronous analytics. |
| EVT-02 | Database-backed duplicate constraints, transactional normalization, idempotent side effects, retries of transient errors with backoff, failed jobs and dead letters. Handle failures between persistence and enqueue. |
| ANALYTICS-01 | PR counts/states, cycle time, first review and review duration; workflow counts, success/failure rates, duration and trends; deployment counts/frequency/reliability/duration; commits, contributors and issue activity. |
| ANALYTICS-02 | Aggregate historical metrics in workers; dashboards read aggregates, not expensive historical scans. Define time windows, denominators, missing data and freshness. |
| UI-01 | Overview, repositories, PRs, CI/CD, deployments, engineering health, AI, alerts, team, integrations, audit and settings; clean B2B presentation, responsive navigation, useful loading/empty/error/stale/unauthorized states. |
| UI-02 | 7/30/90-day and custom windows; repository, author, state and date filters where applicable. Repository overview/PR/CI/deployment/activity views. PR operational states including awaiting review, long-running and recently merged. |
| HEALTH-01 | Explainable workflow-level signals using CI/deployment reliability, cycle times, review latency and trends. Never automatic personnel assessments. |
| ALERT-01 | Configurable threshold/window conditions such as failures in 24h or PR review delay, alert events, email first; future Slack/Teams/webhooks. |
| AI-01 | Provider abstraction, controlled backend tools for repositories/PR/CI/deployments/events/period comparisons/failures. No unrestricted SQL/database access. |
| AI-02 | Tenant and role authorization, evidence and record references, facts distinguished from interpretation, no invented metrics, bounded time/cost and provider-error handling. No paid calls needed for routine tests. |
| KEY-01 | Organization API keys: create, revoke, rotate, last use, one-time secret display, secure hashes rather than plaintext. |
| AUDIT-01 | Record login/logout, invitation/role change, integration connection/disconnection, API key and settings changes with actor, organization, action, resource, timestamp and safe metadata. |
| CACHE-01 | Redis for actual dashboard caching, configurable distributed auth/API/AI rate limiting and short-lived state; coordination only if justified. Tenant-aware keys and invalidation/TTL rules. |
| API-01 | /api/v1, Pydantic request/response schemas, appropriate HTTP status, standardized errors with request IDs, cursor pagination, filtering and sorting. |
| SEC-01 | Server authentication/authorization, tenant boundaries, signed webhooks, secure credentials, input validation, safe logs, environment secrets, production HTTPS and least-privilege IAM. |
| OPS-01 | Structured logging, OpenTelemetry, Prometheus, Grafana: requests/latency/errors, database latency/errors, queue depth, worker and webhook processing, cache hit rate, AI latency/failures. |
| QA-01 | Type hints, module boundaries, repositories/services, DI where helpful, Ruff/MyPy/Pytest, integration/E2E/load tests as appropriate; CI lint/types/tests/images/security checks. |
| CLOUD-01 | Queue local/SQS adapters; storage local/S3 adapters; AWS ECS/Fargate, RDS, ElastiCache, S3, SQS, ALB, IAM, CloudWatch. Terraform without continuous deployment spending. |

## Planned entities

User, Organization, OrganizationMember, Team, Integration, Repository, WebhookEvent, Commit, PullRequest, PullRequestReview, WorkflowRun, Deployment, Metric, Alert, AlertEvent, ApiKey, AuditLog, AiConversation, AiMessage. Issue normalization, invitation records, sessions, daily metric aggregates and durable publication support must be justified during their owning phase. Do not create unused tables.

Foreign keys, unique external identities scoped correctly, tenant-safe relationships, timestamps, transactions, migrations, query-driven indexes and appropriate normalization are mandatory. Do not assume a GitHub identity equals a platform user.

## Acceptance journey

Register → log in → create organization → invite members and enforce roles → connect GitHub → select repositories → initial sync → verify/persist webhook → enqueue → idempotent worker → normalize → aggregate → real dashboard → permission-checked AI tools → evidence-backed answer.

MVP additionally requires retries, secure API errors, meaningful Redis use, critical tests, Docker startup, working CI, observability, and demonstrated negative cross-tenant access tests. A demo UI alone cannot satisfy this acceptance journey.

## Delivery discipline

For each named milestone: requirements, design, smallest correct implementation, tests, local run, review, documentation, then proceed. Ask about material architecture/data design ambiguity; state minor reversible decisions. Major changes require discussion. No unrelated features or inflated resume claims.
