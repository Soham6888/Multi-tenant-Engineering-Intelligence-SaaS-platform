# Initial role and permission matrix

Each request to an organization route first checks active membership in that organization. A missing membership returns the same 404 response as an unknown organization. Frontend controls only improve usability; they do not grant access.

| Capability | OWNER | ADMIN | MANAGER | DEVELOPER | VIEWER |
|---|---:|---:|---:|---:|---:|
| Read organization and member roster | Yes | Yes | Yes | Yes | Yes |
| Read repositories and engineering analytics | Yes | Yes | Yes | Yes | Yes (read-only) |
| Create an organization | Yes (creator becomes owner) | Yes (creator becomes owner) | Yes (creator becomes owner) | Yes (creator becomes owner) | Yes (creator becomes owner) |
| Invite ADMIN | Yes | No | No | No | No |
| Invite MANAGER/DEVELOPER/VIEWER | Yes | Yes | No | No | No |
| Change roles or remove members | Yes | Limited to non-admin members; cannot grant ADMIN | No | No | No |
| Manage organization settings/integrations/API keys | Owner authority | Admin authority | No | No | No |
| Use AI analytics tools | Yes | Yes | Yes | By analytics permission policy | No until read policy is finalized |

The current API implements organization creation/list/detail, member listing, role changes, member removal, and invitation issue/accept. It enforces OWNER/ADMIN boundaries and preserves at least one OWNER. Other capabilities in this matrix describe intended policy for their owning feature phase and are not implemented by placeholder routes. In particular, integrations, API keys, analytics, alerts, and AI endpoints do not yet exist. The viewer/read-only policy for engineering records must be finalized before those endpoints are implemented.

Creating an organization is allowed for any authenticated user; the creator is automatically its OWNER. A pending invitation cannot grant OWNER. Only the authenticated account whose normalized email matches the invitation can accept it, and each token is valid for one acceptance during its seven-day lifetime.
