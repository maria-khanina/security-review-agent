# Writer brief: c043_ledger_service

Author profile `ticket_writer`: Jira style with user stories, numbered requirements and acceptance criteria; non-functional requirements are afterthoughts.
- structure=ticket_style, english=native_fluent, hedging=low, terminology=consistent, staleness=none
- typical gaps: security as acceptance criteria, data classification
- length 900-1700 words; typo rate 0.01; markdown breakage none; dangling references 0; TBD markers 0

Service: Double-entry ledger consumed by wallet and payment services. (Meridian Pay, internal exposure, data: internal)

Components:
- ledger-core (service)
- ledger-db (PostgreSQL) (database)
- ledger-events (Kafka) (message_queue)

Flows:
- Wallet and payment services -> ledger-core: journal entries
- ledger-core -> ledger-db (PostgreSQL): entries and balances
- ledger-core -> ledger-events (Kafka): posted entry events

Implementation (openapi) the document describes:
- POST /v1/entries: Post a balanced journal entry
- GET /v1/entries/{entryId}: Retrieve an entry
- GET /v1/accounts/{accountId}/balance: Get account balance
- POST /v1/entries/{entryId}/reversal: Reverse an entry
- GET /v1/entries: List entries

## Planted items
- F1 [violation, low] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Base images are pinned to old versions and are not rebuilt.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:AUTH-03|...⟧ Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- ⟦S:CRYPTO-04|...⟧ Traffic between services and to data stores must be encrypted in transit.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:CRYPTO-06|...⟧ Encryption keys must be held in KMS, never stored with the data they protect, and rotated at least annually.
- ⟦S:CRYPTO-07|...⟧ Services must validate TLS certificates and must not disable verification.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:NET-04|...⟧ Services calling third parties must have egress restricted to an approved allowlist.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:DATA-04|...⟧ Non-production environments must not contain real personal or card data.
- ⟦S:API-03|...⟧ Outbound and inbound webhook payloads must be signed and signatures verified.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:OPS-02|...⟧ Containers must run as a non-root user with a read-only root filesystem where possible.
- ⟦S:AUTHZ-01|...⟧ Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.
- ⟦S:API-01|...⟧ All external inputs must be validated against a schema and rejected if invalid.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:LOG-04|...⟧ Access to centralized logs must be limited to authorized staff.
- ⟦S:OPS-03|...⟧ Backups must be encrypted and restoration must be tested at least twice a year.
- ⟦S:SECRET-03|...⟧ Service credentials must be rotated at least every 90 days and immediately after suspected exposure.
- ⟦S:LOG-03|...⟧ Audit logs must be tamper-evident and retained for at least one year.

## Functional content (no security claims)
Aim for at least 900 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.
Functional detail to describe for each endpoint:
- POST /v1/entries: request fields debit_account, credit_account, amount, currency, reference; response fields id, debit_account, credit_account, amount, posted_at
- GET /v1/entries/{entryId}: request fields none; response fields id, debit_account, credit_account, amount, posted_at
- GET /v1/accounts/{accountId}/balance: request fields none; response fields account_id, balance, currency
- POST /v1/entries/{entryId}/reversal: request fields reason; response fields id, debit_account, credit_account, amount, posted_at
- GET /v1/entries: request fields none; response fields id, debit_account, credit_account, amount, posted_at

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c043_ledger_service/design_marked.md
