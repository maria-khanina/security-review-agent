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
| NFR-1 | Service authentication | Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected. |
| NFR-2 | Tokens | Tokens are short-lived (15 minutes maximum) and refresh tokens are single-use, so each refresh issues a new one. |
| NFR-5 | Internal transport | Traffic between services, and between services and data stores or brokers, is encrypted in transit. |
| NFR-6 | Algorithms | We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode. |
| NFR-7 | Keys | Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year. |
| NFR-8 | Certificates | TLS certificate verification is enabled in all clients, with no option to disable it. |
| NFR-9 | Secrets in artifacts | No secrets are kept in source code, config files, API specs or infrastructure definitions. |
| NFR-10 | Secrets at runtime | On boot, the service pulls its credentials from the approved secret store. |
| NFR-12 | Network | ledger-db and the Kafka brokers sit in private subnets and are not publicly reachable. |
| NFR-13 | Egress | Outbound calls to third parties are restricted to an approved allowlist. |
| NFR-14 | Security logging | We log failed logins, changes of privileges and reads of sensitive data. |
| NFR-16 | Test data | Real customer and card data is kept out of dev, test and staging. |
| NFR-17 | Callbacks | Webhook payloads, inbound and outbound, carry an HMAC signature and a timestamp, and the receiver verifies both. |
| NFR-18 | Queries | We use parameterized queries only, with no SQL built from user input by string concatenation. |
| NFR-19 | Pipeline | Base images are pinned to old versions and are not rebuilt, so the scanner results never change. |
| NFR-20 | Containers | Containers run as a non-root user, with a read-only root filesystem where possible. |

The service compares the authenticated caller with the owner of the requested resource and rejects the request if they do not match and no entitlement exists.
Requests from outside are checked against the schema and rejected if they do not conform.
Admin and debug endpoints are reachable only from the internal network, not from the public internet.
Only the support engineers of this service and the security analysts can read the central logs, because they use them to resolve customer tickets and to review security events; nobody else has access.
Audit logs are written to tamper-evident storage with at least one year of retention.
Encrypted backups are checked by a restoration exercise at least twice a year.
We rotate service credentials at least every 90 days and straight away after any suspected exposure.

## Design notes

Posting is transactional: the entry and the outbox row that drives the event are written in one database transaction, and a relay publishes the event afterwards. Balances are never stored; they are derived from entries by a query on the account index, with a materialized view considered if the read load grows. Reversal is implemented as a normal posting with swapped sides and a link to the original entry.

## Definition of done

- Acceptance criteria demonstrated in staging.
- OpenAPI file updated and published.
- Reconciliation job compares the sum of entries with the sum of balances every night.
