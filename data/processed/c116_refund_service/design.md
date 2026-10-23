**refund service - design** (pasted from #payments-refunds, thread was long so i cut it down)

**timo:** ok so summary of where we are, correct me

**what it is**
refunds gateway (people also say "refund api") takes refund requests from merchants + support, passes them to refund-core, core stores in refund-db (PostgreSQL) and puts a status event on refund-events (Kafka). ledger + notifier consume the events

**api** (5 calls)
• `POST /v1/refunds` - body payment_id, amount, currency, reason, requested_by -> id, payment_id, status, amount, currency
• `GET /v1/refunds/{refundId}`
• `GET /v1/refunds` - filter by status, payment_id
• `POST /v1/refunds/{refundId}/approval` - decision, comment
• `POST /v1/refunds/{refundId}/cancellation` - reason

**mira:** and the rules?

**timo:** sum of refunds per payment can't go above the payment, small ones auto approved (limit TBD), bigger ones need a second person, pending can be cancelled, failed ones go to ops. not 100% sure on the limit numbers

**mira:** security?

**timo:** right, from memory:

*auth / access*
• Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.
• Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.
• Administrative and debug endpoints are not reachable from the public internet.

*data / crypto*
• Personally identifiable information is encrypted at rest with AES-256.
• Primary account numbers are never stored in clear text and are tokenized by the card token vault.
• Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.

*secrets*
• Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
• Runtime secrets are fetched from the approved secret store at startup.

**mira:** what about the db side and input handling?

**timo:** refund-core reads and writes the refund records in refund-db (PostgreSQL) for every request. and for input The API accepts any JSON object, and the service picks the fields that it needs. (we said we'd tighten it later)

**mira:** and limits?

**timo:** Rate limiting is left for a later release, and there are no per-client limits at launch. TBD who owns it

*more*
• Authentication failures, privilege changes and access to sensitive data are logged.
• Logs contain no secrets, card numbers or personal data beyond opaque identifiers.
• Personal data has a defined retention period and is deleted when it expires or on a verified request from the data subject.
• Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.
• Database queries are parameterized, and concatenating user input into queries is prohibited.
• Browser-facing APIs allow only approved origins in CORS.
• The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.

**mira:** ok, open: retention for completed refunds? TBD. also who gets the alert on weekends TBD

**timo:** yeah. will write it up properly next week (TBD)
