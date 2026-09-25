# ADR-005: GitHub authorization and tenant binding

Date: 2026-09-24. Status: **Accepted: GitHub App with OAuth user verification; one installation belongs to one platform workspace.**

Requirements: GH-01, TEN-01, RBAC-01, SEC-01. This proposal does not amend the master specification's OAuth requirement. No integration, credentials, migrations or live connection are implemented by this ADR.

## Options

| Concern | GitHub App with OAuth user verification (recommended) | OAuth App |
|---|---|---|
| Organization access | Installation grants account/repository access; worker access can survive the installing user's departure | Access follows the authorizing user and organization policies |
| Repository selection | GitHub installation selection limits provider access; platform selection further limits tracking | Platform selection limits tracking, but OAuth scopes may grant broader provider access |
| Permissions | Fine-grained repository permissions | Scope-based access; private repository analytics generally needs broad `repo` access |
| Credentials | App private key mints short-lived installation tokens; user OAuth verifies the connecting identity | User access/refresh token lifecycle and organization authorization must be handled |
| Webhooks | Central app webhook with installation lifecycle events | Individual repository/organization hooks and their cleanup |

These provider differences are documented in [GitHub's comparison](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/differences-between-github-apps-and-oauth-apps). A GitHub App can use OAuth, but choosing it still requires the explicit decision called for in the development plan.

## Proposed binding invariant

Recommend that one GitHub installation has at most one active platform organization binding. A platform organization may connect several installations. Identify the provider account, installation and repository by immutable GitHub IDs; names are display attributes.

Enforce active installation uniqueness using provider host, app ID and installation ID. Repository identity is unique within the platform organization and provider host; tenant-safe relationships must prevent attaching a repository to another organization's integration. Preserve repository identity across reconnects and renames. Verify account/installation ownership before updating an existing binding.

Sharing an installation across platform organizations is the alternative. It requires explicit per-tenant repository selection, webhook fan-out, independent retention and disconnect semantics. This materially changes constraints and event routing; do not implement either invariant without the user's choice. Reassignment after disconnect must verify fresh authorization and must never move the old tenant's historical records to the new tenant.

## Proposed connection security contract

1. An authenticated OWNER or ADMIN starts connection for an organization. Apply current membership checks, CSRF/origin guards and request limits. Recheck the role at callback completion under the organization lock.
2. Generate short-lived, single-use random state. Store only its digest, with platform user, session, organization, intended operation and expiry. Atomically claim it on callback. Failed/replayed attempts require a new connection flow. Use fixed allowlisted callback/return URLs.
3. Exchange the OAuth code only on the server, validate state and session, and use the resulting user token to verify access to the proposed installation. A setup URL's `installation_id` alone is untrusted: [GitHub explicitly warns about spoofed installation IDs](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/about-the-setup-url). Validate the installation belongs to the configured app and enforce provider-side administration authority for connection, not merely repository visibility. The endpoint/permission proof needs fixture coverage before implementation acceptance.
4. Commit the binding and safe audit record transactionally. Reject an already-bound installation without revealing another tenant's details. Do no historical import in the callback.
5. Enumerate accessible repositories with bounded pagination. A selection mutation verifies each ID belongs to the active installation and tenant. Installation access and selected tracking are separate states.

Recommend repository Metadata read for discovery. Add Contents read, Pull requests read, Issues read, Actions read and Deployments read when the corresponding event/sync paths arrive. Validate exact endpoint and event permission requirements against official documentation in each implementation slice; no write access or organization-member access is proposed. See [choosing permissions](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app).

## Credential and revocation contract

Keep the app private key, client secret and webhook secret outside source control, supplied through environment/file references with restricted local access. Do not persist installation tokens; mint narrowly scoped tokens as needed and retain them only in bounded process memory before expiry. GitHub documents token generation and repository narrowing in [installation token guidance](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app).

Use the user OAuth token only for binding verification and discard it after the exchange. If persistent user credentials become necessary, stop and specify authenticated encryption with an externally held, versioned key before storing them. Never log provider responses containing credentials, authorization headers, OAuth query strings or raw state. Sanitize callback errors and frontend redirects.

Disconnect first disables local access transactionally, advances a connection generation, clears token caches and records an audit event. Jobs must verify active integration, tenant, selected repository and generation before provider calls and before committing results. Attempt revocation of held provider tokens; report cleanup failures separately. Local disconnect is distinct from uninstalling the app on GitHub. Suspended/deleted installations and removed repositories must disable corresponding work when provider lifecycle events arrive; fail closed on confirmed access loss in the meantime.

## Catalog and synchronization boundary

The injected provider client needs bounded connection/read/total timeouts, an allowlisted API host, safe pagination, bounded response sizes and sanitized errors. Distinguish missing/revoked access from primary/secondary rate limiting; respect provider retry timing and use capped retry policy for transient failures. Never follow provider pagination links to arbitrary hosts or forward tokens across redirects.

Expose catalog availability and tracking state independently of engineering sync progress. Historical sync remains pending until the durable queue and normalization phases exist. Later jobs persist checkpoints, recheck authorization and resume pages; the historical import window remains a user decision. No synchronous callback import or simulated completed-sync state.

## Acceptance and decision

Fixture tests must cover role/cross-tenant denial; expired, mismatched and replayed state; spoofed installation IDs; concurrent binding claims; multi-page catalogs; foreign repository selection; rate limits; secret redaction; revocation and disconnect during jobs. Live authorization needs a user-owned app and credentials. Live webhooks additionally need an approved reachable endpoint; no tunnel, app registration or publication is authorized by this proposal.

User decisions on 2026-09-24: GitHub App with OAuth user verification and exclusive installation binding approved. An installation belongs to one platform workspace. The comparison and proposed contracts above record the rationale; the authorization/binding decision gate is satisfied. Next implement only the integration/catalog schema and tested provider client slice, then connection/selection routes and UI. The detailed security contracts remain subject to implementation verification.
