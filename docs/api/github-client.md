# GitHub catalog client contract

Implemented in `backend/app/integrations/github.py`, under accepted ADR-005. This internal adapter is not exposed as an HTTP route. No app registration, OAuth callback, token minting, repository selection API or live sync is implemented yet.

`GitHubClient.repositories(SecretStr(token), page=1)` returns validated repository summaries and a next-page number. The caller supplies a verified installation token and is responsible for organization authorization and checking integration generation. Only GitHub.com is supported. Test transport injection allows deterministic tests without credentials or paid resources.

- Fixed HTTPS API host, no redirects or environment proxies; pagination constructs the next request locally and never follows a Link URL to another host.
- At most 100 repositories per page, 2 MB decoded response, page range 1–10000, 8-second HTTP timeout (3-second connect) and 20-second total deadline per operation.
- Transport/server failures receive one retry after 200 ms. Exhaustion reports a retryable error. Rate limits return a scheduling hint and do not sleep/retry inline; workers will own durable scheduling in their phase.
- 401/403/404 produce an access-denied error, not proof of uninstallation. A 403 with rate-limit headers is classified separately. Ambiguous forbidden responses must not cause destructive revocation. Revocation verification belongs to the connection service.
- Errors omit provider bodies, credentials and request URLs. Installation credentials exist only in the caller's memory; no token logging or persistence is added.

Implementation references checked 2026-09-24: [installation repository enumeration](https://docs.github.com/en/rest/apps/installations#list-repositories-accessible-to-the-app-installation), [REST API best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api). API version is pinned to `2026-03-10` as shown in current official endpoint documentation.

Next slice: OAuth single-use state, user/installation administration proof, token lifecycle, transactionally authorized connection/disconnection, paginated tenant catalog and selection API, then real workspace integration UI. The present adapter does not establish the OAuth security contract on its own.
