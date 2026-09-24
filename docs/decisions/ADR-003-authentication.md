# ADR-003 — Revocable cookie sessions

Status: implemented and verified against PostgreSQL and browsers. Production deployment remains future work.

## Context

The initial client is a first-party browser app. Registration, login, logout and current-user identity must work before organizations. A browser profile label is not authentication. Logout must revoke a credential immediately.

## Decision

Use random 256-bit opaque session tokens in HttpOnly, SameSite=Lax cookies. Store only SHA-256 token digests in PostgreSQL with a fixed configurable expiry (12 hours initially). Production uses Secure and a __Host- cookie name, HTTPS origins, no Domain attribute, and Path=/. A new login creates a new token and revokes the browser's previous token. Logout deletes the matching database session.

Use Argon2id (64 MiB, 3 iterations, parallelism 4), offloaded to the thread pool. Unknown users use a dummy hash verification. Email identity is normalized and case-insensitive by documented application policy, protected by a database uniqueness constraint. Passwords are 15–128 characters with no silent trimming or composition rules.

The Next.js same-origin proxy forwards only auth operations. Browser POST requests need an exact configured Origin and X-EIP-Request: 1. No permissive CORS is enabled. Logout also requires a session-bound CSRF value returned by login/register/me; the value is a domain-separated hash of the random credential. It grants no session access and is never stored in browser persistent storage. JSON responses are no-store. Client IP for limits comes from the transport, never arbitrary X-Forwarded-For. The first proxy deployment shares a conservative IP bucket until a trusted-proxy policy is implemented.

Redis atomically increments expiring counters for IP and normalized-account buckets before password work. Redis failure denies auth writes with 503. No raw emails or passwords appear in keys. Session/user/audit writes commit together. A reusable backend dependency enforces current-user access; no organization permissions are inferred yet.

## Reason

Server sessions provide simple immediate revocation and keep browser credentials out of localStorage. PostgreSQL remains authoritative. Redis solves a real distributed abuse-control requirement. CSRF is explicit rather than relying only on SameSite. ADR-004 documents organization authorization and initial workspace roles.

## Alternatives

Stateless JWTs complicate immediate revocation and refresh-token rotation without helping this first-party browser workflow. Bearer tokens in localStorage increase exposure to script access. OAuth/SSO are future integration work, not prerequisites for local account authentication.

## Consequences

Every authenticated request performs a database lookup. Deployment must preserve cookies and request Origin, use HTTPS and configure trusted origins. The proxy currently shares IP throttling across clients, which is conservative but unsuitable for large shared deployments. Account verification, recovery, MFA, session management UI and retention/pruning are future work. Authentication does not implement tenancy.

References: [OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).
