# Ledger Service: stories and design

Epic: LEDGER-60 (Ledger, second consumers)
Status: Ready for development

## Overview

The ledger is already live for wallet balances. This epic opens it to a second group of consumers (payments and reporting) and adds reversal and listing support. ledger-core receives entries from the wallet and payment services, stores them in ledger-db (PostgreSQL) and publishes a posted-entry event on ledger-events (Kafka).

## Stories

### LEDGER-61: Post an entry from the payment service

As the payment service, I want to post a balanced entry for each captured payment so that the ledger shows the movement of money.

Acceptance criteria:
- POST /v1/entries accepts debit_account, credit_account, amount, currency and reference.
- The reply has id, debit_account, credit_account, amount and posted_at.
- An entry whose two sides use different currencies is rejected with a clear message.
- Posting the same reference twice returns the original entry and does not create a second one.
- The posted-entry event is published after the commit and carries the entry id.

### LEDGER-62: Reverse an entry

As a finance operator, I want to reverse an entry so that a mistake is corrected without editing history.

Acceptance criteria:
- POST /v1/entries/{entryId}/reversal accepts a reason and posts an entry with the sides swapped.
- The reversal references the original entry.
- An entry can be reversed once.
- The original entry is never changed.

### LEDGER-63: Read entries and balances

As the reporting service, I want to read entries and balances.

Acceptance criteria:
- GET /v1/entries/{entryId} returns one entry.
- GET /v1/entries lists entries, newest first.
- GET /v1/accounts/{accountId}/balance returns account_id, balance and currency; the balance equals the sum of the account's entries.

### LEDGER-64: Nightly reconciliation

As finance, I want a nightly check that the sum of all entries equals the sum of all balances.

Acceptance criteria:
- The job runs after midnight UTC and writes its result to the finance channel.
- Any difference raises a page to the on-call finance engineer.

## Non-functional requirements

These apply to all stories above.

| ID | Area | Requirement |
|---|---|---|
| NFR-2 | Algorithms | ⟦S:CRYPTO-05|Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.⟧ |
| NFR-3 | Secrets in artifacts | ⟦S:SECRET-01|Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.⟧ |
| NFR-4 | Secrets at runtime | ⟦S:SECRET-02|At startup the service fetches its secrets from the approved secret store.⟧ |
| NFR-6 | Security logging | ⟦S:LOG-01|We log failed logins, changes of privileges and reads of sensitive data.⟧ |
| NFR-7 | Queries | ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧ |
| NFR-8 | Pipeline | ⟦S:OPS-01|CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧ |

## Design notes

Posting is transactional. The entry and an outbox row are written in one database transaction, and a relay publishes the event afterwards, which guarantees that an event is never published for an entry that was not committed. Balances are never stored; they are derived from entries by a query on the account index. If the read load grows, a materialized view refreshed after each commit is the planned next step.

The list endpoint uses keyset pagination on the posting time and the entry id, because offset pagination becomes slow once the table holds hundreds of millions of rows. The page size is fixed at the service level so that clients cannot request unbounded pages.

Reversal is implemented as a normal posting with the debit and credit accounts swapped and a link to the original entry. Because the original is never modified, the audit trail of a correction is complete: the reader sees the mistake, the reversal and the corrected entry in order.

## Rollout

Payments are enabled per merchant segment behind a feature flag. Reporting starts reading from the ledger in shadow mode and compares its figures with the existing reports for two weeks before switching over. A rollback of either consumer is a configuration change.

## Definition of done

- Acceptance criteria demonstrated in staging.
- OpenAPI file updated and published.
- Reconciliation job and its alert exist and have been exercised once with an injected difference.
