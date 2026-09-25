# Security model

## Authentication now implemented

- New users choose a 15–128 character passphrase; Argon2id stores salted hashes, never plaintext. Password work runs off the event loop and is concurrency-bounded. Unknown-account login verifies against a dummy hash and returns the same message as a wrong password.
- PostgreSQL stores only SHA-256 digests of random opaque 256-bit browser session credentials. Sessions expire after a configurable 12-hour default. Login rotates any existing browser session; logout deletes it immediately. Browser credentials use HttpOnly/SameSite=Lax cookies with no Domain. Production requires HTTPS, a Secure `__Host-` cookie, and configured HTTPS origins.
- Login/registration/logout mutations require an exact allowed Origin and custom `X-EIP-Request` header. Logout also checks a session-bound CSRF digest. Auth responses are no-store.
- The same-origin Next.js proxy allowlists auth and organization methods, filters forwarded cookies and headers, enforces a 16 KiB request size, uses a fixed timeout and refuses redirects. It returns generic upstream failures.
- Redis atomically applies expiring IP and account attempt limits. Account/IP keys are hashed; Redis failure denies auth writes. Defaults are 30/IP, 10/account per five minutes.
- Each successful registration/login and logout writes an audit record in the same PostgreSQL transaction as the session change. Organization creation, role changes, member removal, and invitation issue/accept write organization-scoped audit records. No audit read endpoint exists yet.
- Production environment validation rejects HTTP origins. Secret-managed DB/Redis configuration and production HTTPS termination remain deployment work.

## Proxy rate-limit constraint

Local Next.js-to-API requests share one server-side IP address. Per-account limits still distinguish accounts; the IP bucket is a shared guard. Before production, configure trusted proxy handling so the API can obtain client addresses only from known infrastructure. Do not trust arbitrary `X-Forwarded-For` values.

## Before public deployment or tenant data

Implement account verification, credential recovery, account lifecycle policy and session cleanup. Review trusted proxy and TLS configuration, production CSP, secret management, encryption at rest, least-privilege IAM and retention. This auth milestone is not a deployment approval.

Organization endpoints authorize membership and role on every request, return indistinguishable not-found responses for nonmember organization IDs, and enforce a last-owner invariant while serializing owner changes on the organization row. Admins cannot manage owners/admins or assign administrator roles. Invitations store only a token digest, match the authenticated account email, expire after seven days and are consumed once. Email is not verified and no delivery mechanism exists, so the invitation token must be delivered privately out-of-band. All future SQL, aggregates, cache, jobs, storage and AI tools must continue to scope by tenant; cross-tenant negative tests are release gates.

Before live GitHub, protect OAuth state/callbacks, limit scopes, protect integration secrets, verify signatures on exact raw bodies, enforce payload limits and bind each integration to the correct authorized tenant. Idempotency is required.

AI tools must enforce authorization independently of model instructions. Never provide unrestricted SQL/database credentials to a model. Restrict tool schemas/output sizes, provide evidence, bound calls, distinguish observation from interpretation, and treat repository content as untrusted.

## Remaining limitations

Organization APIs have an initial tenant boundary; GitHub webhook security, verified email, complete CSP, production TLS proxy, managed secret vault, audit listing and public deployment do not exist yet. Use local development only until a separate production hardening review is complete.

Security references: [OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).

## Tenancy repair

All membership mutations acquire the organization row lock before loading current actor and target roles. Requests waiting behind a demotion/removal recheck current permissions. Invitations use the same lock order, refresh after waiting, and verify that their issuer still has authority when accepted. Concurrent acceptance cannot create duplicate memberships. Role changes, tenant writes, expiry/wrong-email/replaced-token rejection, concurrent owner demotions, and fail-closed API limits have regression tests against PostgreSQL.

All API responses are no-store. Body-size checks also cover organization writes. Organization API budgets use authenticated user identifiers rather than trusting forwarded IP headers.
