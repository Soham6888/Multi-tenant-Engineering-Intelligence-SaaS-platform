# Database plan

Migrations 0001–0003 create users, sessions, audit logs, organizations, memberships, invitations, and tenant-linked audit records.

`organization_members` is unique on `(organization_id, user_id)` and role-constrained. `organization_invitations` is unique on `(organization_id, email)` and token hash, with an explicit non-owner role constraint and expiry. Invitation tokens are single-use bearer secrets represented at rest only by SHA-256 digests. The raw token is returned once to the administrator for delivery; email delivery and verified identity are not implemented. `audit_logs.organization_id` is nullable so pre-tenant account events remain valid and tenant actions can be scoped.

Subsequent GitHub entities use external IDs and tenant-scoped ownership. Audit security-sensitive mutations in the same transaction where feasible.

GitHub authors/reviewers may not be platform users; choose an external identity representation during GitHub modeling rather than attaching arbitrary GitHub IDs to User foreign keys. Raw events require durable delivery uniqueness. Every tenant-owned relationship must preserve the tenant boundary, including child entities reached through repositories.

Daily metric aggregates need enough counts/sums to recompute weighted window values: do not average averages. Define UTC boundaries, success denominators, excluded workflows and missing timestamps before implementing analytics. Index based on concrete query patterns (tenant/repository/time, delivery/external IDs, foreign keys), with documented rationale.

## Conceptual ERD — future, not a migration

```mermaid
erDiagram
    User ||--o{ OrganizationMember : joins
    Organization ||--o{ OrganizationMember : has
    Organization ||--o{ Integration : connects
    Organization ||--o{ Repository : owns
    Organization ||--o{ WebhookEvent : receives
    Repository ||--o{ PullRequest : contains
    PullRequest ||--o{ PullRequestReview : receives
    Repository ||--o{ WorkflowRun : executes
    Repository ||--o{ Deployment : releases
    Repository ||--o{ DailyMetric : aggregates
```
