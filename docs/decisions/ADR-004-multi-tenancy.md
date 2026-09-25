# ADR-004 — Organization-scoped tenancy and membership roles

## Context

Organizations own all engineering data. A caller-controlled organization ID is not proof of access; membership must be checked by the backend on every scoped request. The first release needs a useful workspace setup flow without introducing database row-level security or a complex policy engine prematurely.

## Decision

Use a shared PostgreSQL schema with UUID primary keys, explicit organization foreign keys and a unique `(organization_id, user_id)` membership. Every organization route resolves the signed-in user's membership before reading tenant data. Hide unauthorized organizations with the same 404 response used for missing organizations. Roles are `OWNER`, `ADMIN`, `MANAGER`, `DEVELOPER`, and `VIEWER`; owners administer all roles, while admins can administer only non-admin roles and cannot grant ADMIN. Serialize owner removal/demotion through a lock on the organization row and preserve at least one OWNER.

Invitations are seven-day, single-use random bearer tokens. Persist only a SHA-256 digest, bind acceptance to an authenticated matching email, and replace a prior invitation to the same address. Since no email sender or email-verification system exists, the issuing administrator receives the token once for private out-of-band delivery; the product makes no claim to deliver or verify it.

## Reason

This is easy to run locally and keeps tenant ownership explicit and testable. Database uniqueness and role checks protect core invariants; service authorization prevents IDOR. A shared schema matches the initial SaaS scale and avoids premature per-tenant databases or PostgreSQL RLS operational complexity.

## Alternatives

- Trust frontend filtering or organization IDs: rejected because it fails server-side isolation.
- Database-per-tenant: rejected because it adds disproportionate migration and connection management.
- PostgreSQL RLS: reconsider if additional defense in depth becomes worthwhile; current transaction/session management does not yet set tenant context centrally.
- Email invitation: deferred until a safe, budget-compatible delivery and verified-email workflow exists.

## Consequences

Positive: local-first, testable tenant isolation, auditable membership changes, simple organization-scoped SQL.

Negative: every future tenant query, cache key, worker message, storage object and AI tool must preserve tenant scope. Email ownership is not verified. Audit records can identify the organization but the read endpoint is not implemented. Role rules remain deliberately small and must be expanded explicitly as product permissions grow.

## Authorization concurrency clarification

Acquire the organization row lock before loading actor and target membership state for role mutations, removal and invitation issuance. Invitation acceptance acquires the same lock and reloads both token validity and issuer authority. This serializes competing permission changes and prevents an invitation issued by a subsequently unauthorized member from granting access. Concurrent regression tests exercise these guarantees with PostgreSQL.
