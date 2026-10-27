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
• ⟦S:AUTH-01|Public endpoints reject any call that carries neither a valid OAuth2 bearer token nor a client certificate.⟧
• ⟦S:AUTHZ-01|Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.⟧
• ⟦S:AUTHZ-04|Admin and debug endpoints are reachable only from the internal network, not from the public internet.⟧

⟦S:CRYPTO-04|Connections to the database and between internal services use TLS.⟧

*data / crypto*
• ⟦S:CRYPTO-01|Personal data is encrypted at rest with AES-256.⟧
• ⟦S:CRYPTO-02|Primary account numbers never reach our storage in clear text, because the card token vault tokenizes them first.⟧
• ⟦S:CRYPTO-05|The approved algorithm list is followed, and MD5, SHA-1, DES, 3DES and ECB mode are prohibited in this service.⟧

*secrets*
• ⟦S:SECRET-01|Source, config, specs and infrastructure definitions contain no secrets.⟧
• ⟦S:SECRET-02|At startup the service fetches its secrets from the approved secret store.⟧

⟦S:CRYPTO-03|Only TLS 1.2 and TLS 1.3 are accepted for connections from outside.⟧

**mira:** what about the db side and input handling?

**timo:** ⟦F2|refund-core reads and writes the refund records in refund-db (PostgreSQL) for every request.⟧ and for input ⟦F1|The API accepts any JSON object, and the service picks the fields that it needs.⟧ (we said we'd tighten it later)

**mira:** and limits?

**timo:** ⟦F3|Rate limiting is left for a later release, and there are no per-client limits at launch.⟧ TBD who owns it

⟦S:NET-01|The database and the message broker are in private subnets with no public address.⟧

*more*
• ⟦S:LOG-01|Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.⟧
• ⟦S:LOG-02|Log lines are kept free of secrets, card numbers and personal details, and identifiers are opaque.⟧
• ⟦S:DATA-02|We keep personal data for 12 months at most and delete it automatically when the period ends, or earlier on a verified request.⟧
• ⟦S:DATA-03|The vendor receives the customer id and the email only, as these are the fields its notification task needs, and a data processing agreement covers the transfer.⟧

⟦S:AUTH-02|Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.⟧
⟦S:OPS-03|Backups are encrypted, and restores are tested at least twice a year.⟧
⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧
• ⟦S:API-05|All queries use bound parameters instead of string concatenation.⟧
• ⟦S:API-06|CORS allows only approved origins.⟧

⟦S:AUTH-03|A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use.⟧
• ⟦S:OPS-01|Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks.⟧

**mira:** ok, open: retention for completed refunds? TBD. also who gets the alert on weekends TBD

**timo:** yeah. will write it up properly next week (TBD)
