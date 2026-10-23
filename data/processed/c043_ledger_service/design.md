# Ledger Service: stories and design

Epic: LEDGER-30 (Standalone ledger)
Status: Ready for development

## Overview

The ledger moves out of the payments monolith into its own service, ledger-core, with its own database, ledger-db (PostgreSQL), and its own event stream, ledger-events (Kafka). Wallet and payment services call ledger-core to post entries; ledger-core writes them to ledger-db and publishes a posted-entry event.

## Stories

### LEDGER-31: Post an entry

As a wallet service, I want to post a balanced journal entry so that the movement of money is recorded.

Acceptance criteria:
- POST /v1/entries accepts debit_account, credit_account, amount, currency and reference.
- The reply contains id, debit_account, credit_account, amount and posted_at.
- Entries whose sides use different currencies are rejected.
- Posting the same reference twice returns the original entry.

### LEDGER-32: Read an entry and a balance

As a payment service, I want to read entries and balances.

Acceptance criteria:
- GET /v1/entries/{entryId} returns one entry.
- GET /v1/accounts/{accountId}/balance returns account_id, balance and currency.
- GET /v1/entries lists entries, newest first.

### LEDGER-33: Reverse an entry

As a finance operator, I want to reverse an entry so that mistakes can be corrected without editing history.

Acceptance criteria:
- POST /v1/entries/{entryId}/reversal accepts a reason and posts a cancelling entry.
- An entry can be reversed only once.
- The original entry is never changed.

### LEDGER-34: Publish posted entries

As a downstream consumer, I want an event for each posted entry.

Acceptance criteria:
- An event is published to ledger-events after the entry is committed.
- Events are delivered at least once and carry the entry id, so consumers can de-duplicate.

## Non-functional requirements

Listed once for the whole epic (TBD: copy into each story as acceptance criteria).

| ID | Area | Requirement |
|---|---|---|
| NFR-1 | Service authentication | Internal service calls to ledger-core are authenticated with mutual TLS or signed workload identity tokens. |
| NFR-2 | Tokens | Access tokens expire within 15 minutes, and refresh tokens are rotated on use. |
| NFR-5 | Internal transport | Traffic between services, and between services and data stores or brokers, is encrypted in transit. |
| NFR-6 | Algorithms | Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited. |
| NFR-7 | Keys | Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually. |
| NFR-8 | Certificates | Services validate TLS certificates and never disable verification. |
| NFR-9 | Secrets in artifacts | Secrets do not appear in source code, configuration files, specifications or infrastructure definitions. |
| NFR-10 | Secrets at runtime | Runtime secrets are fetched from the approved secret store at startup. |
| NFR-12 | Network | ledger-db and the Kafka brokers sit in private subnets and are not publicly reachable. |
| NFR-13 | Egress | Services that call third parties have their egress restricted to an approved allowlist. |
| NFR-14 | Security logging | Authentication failures, privilege changes and access to sensitive data are logged. |
| NFR-16 | Test data | Non-production environments do not contain real personal or card data. |
| NFR-17 | Callbacks | Webhook payloads, outbound and inbound, are signed and the signatures are verified. |
| NFR-18 | Queries | Database queries are parameterized, and concatenating user input into queries is prohibited. |
| NFR-19 | Pipeline | The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days. |
| NFR-20 | Containers | Containers run as a non-root user, with a read-only root filesystem where possible. |

## Design notes

Posting is transactional: the entry and the outbox row that drives the event are written in one database transaction, and a relay publishes the event afterwards. Balances are never stored; they are derived from entries by a query on the account index, with a materialized view considered if the read load grows. Reversal is implemented as a normal posting with swapped sides and a link to the original entry.

## Definition of done

- Acceptance criteria demonstrated in staging.
- OpenAPI file updated and published.
- Reconciliation job compares the sum of entries with the sum of balances every night.
