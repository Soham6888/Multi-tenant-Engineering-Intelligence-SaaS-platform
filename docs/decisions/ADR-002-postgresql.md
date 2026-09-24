# ADR-002 — PostgreSQL as the system of record

Status: accepted from the user's product specification.

## Context

Organizations, memberships, repositories and events have relational ownership, unique identities and transactional consistency needs. Analytics also require filtered historical queries and aggregates.

## Decision

Use PostgreSQL with SQLAlchemy and Alembic. Introduce tables with their owning feature, starting with authentication. Use database constraints and transactions for integrity, then query-driven indexes. Redis remains auxiliary.

## Reason

Foreign keys and uniqueness protect relationships and event identity under concurrency. Transactions support durable changes. SQL suits aggregate retrieval; precomputed tables limit dashboard query cost.

## Alternatives

SQLite cannot substitute for PostgreSQL integration behavior and concurrency validation. Document-only persistence would complicate ownership and referential guarantees. Redis is not the authoritative domain store.

## Consequences

Requires a PostgreSQL service for integration tests and local full-stack readiness. Migration discipline and tenant-safe query design are mandatory. Foundation readiness alone is not schema validation.
