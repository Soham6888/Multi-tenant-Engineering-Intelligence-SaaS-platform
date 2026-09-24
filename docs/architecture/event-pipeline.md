# Event pipeline — design constraints, not implemented

1. Verify the signature against the exact request body before accepting a delivery.
2. Resolve the tenant from a verified integration; never trust a payload organization ID as platform authorization.
3. Persist raw delivery identity, type, payload, tenant and processing state in a transaction with unique constraints.
4. Reliably arrange publication. A successful database commit followed by a failed queue send must not lose work. Evaluate a transactional outbox at the event-pipeline milestone and record the ADR.
5. Separate worker processes receive jobs, validate/normalize entities, commit idempotently, and acknowledge only after durable completion.
6. At-least-once delivery requires idempotent processing beyond duplicate webhook receipt. Race conditions must be handled by database constraints and transactions.
7. Retry transient network/timeouts/connectivity/provider failures with bounded exponential backoff; invalid payload/authentication/permissions go to an explicit failed state. Exhausted retries enter dead-letter handling.
8. Analytics consume normalized data asynchronously; dashboards expose freshness and eventual consistency.

Local queue implementation must work across independent processes, support retries and acknowledgement semantics, and survive expected development restarts. A process-local list is insufficient. Choosing its durable implementation is deferred to the queue design phase; do not assume Redis is the queue merely because it exists.

GitHub out-of-order updates, webhook redelivery, initial-sync overlap, deleted/renamed repositories, and rate limits need integration tests. Define raw-payload retention, sensitive-data handling and replay authorization before processing real organization data.
