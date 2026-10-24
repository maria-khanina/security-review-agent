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
| NFR-2 | Algorithms | Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not. |
| NFR-3 | Secrets in artifacts | Secrets stay out of the repository: not in code, configuration, specs or infrastructure files. |
| NFR-4 | Secrets at runtime | At startup the service fetches its secrets from the approved secret store. |
| NFR-6 | Security logging | Access to customer records is not recorded anywhere in the ledger. |
| NFR-7 | Queries | Database queries are parameterized, and concatenating user input into queries is prohibited. |
| NFR-8 | Pipeline | Nothing scans the dependencies or the images, and the versions were pinned years ago. |

Admin and debug endpoints are reachable only from the internal network, not from the public internet.
We do not trust the internal network by itself: every internal call is authenticated with mTLS or workload identity tokens.
In-transit encryption covers calls between services as well as connections to databases and queues.

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

# Reference material for the ledger

## Chart of accounts

Accounts are grouped into classes by the first digit of the number. The classes follow the usual double-entry layout.

| Class | Meaning | Examples |
|---|---|---|
| 1 | assets | 1100 customer funds, 1200 funds at acquirers |
| 2 | liabilities | 2100 wallet balances, 2200 merchant payables |
| 3 | equity | 3100 retained result |
| 4 | income | 4100 payment fees, 4200 payout fees |
| 5 | expenses | 5100 acquirer fees, 5200 refunds written off |

Every wallet has its own account in class 2, every merchant its own account in class 2, and the platform accounts in the other classes are shared. Account numbers have the form `class-group-id`, for example `2100-0001-5521`.

## Entry model

An entry moves one amount from a debit account to a credit account. The amount is a positive whole number in minor units. Complex bookings use several entries with the same booking reference.

| Field | Meaning |
|---|---|
| id | identifier of the entry |
| debit_account | account that is debited |
| credit_account | account that is credited |
| amount | positive whole number in minor units |
| currency | ISO 4217 code |
| reference | text that links the entry to the business event |
| posted_at | time of posting, UTC |

### Posting rules

- Debit and credit accounts must differ.
- Both accounts must exist and be open.
- The currency of the entry must be the currency of both accounts.
- An entry is posted exactly once; the posting time is set by the ledger.
- Entries are never changed and never removed.

## Typical bookings

**Capture of a card payment of 100.00 EUR with a fee of 1.50 EUR.**

| Entry | Debit | Credit | Amount |
|---|---|---|---|
| 1 | 1200 funds at acquirers | 2200 merchant payable | 10000 |
| 2 | 2200 merchant payable | 4100 payment fees | 150 |

**Wallet transfer of 15.50 EUR.**

| Entry | Debit | Credit | Amount |
|---|---|---|---|
| 1 | 2100 wallet of the sender | 2100 wallet of the receiver | 1550 |

**Reversal of the transfer.** The reversal is a new entry with debit and credit swapped and a reference to the original entry. The original stays in the ledger.

## Balances

The balance of an account is the sum of its credits minus the sum of its debits for accounts of class 2, 3 and 4, and the opposite for classes 1 and 5. The ledger keeps a running balance with each account to avoid summing all entries on every read. The nightly check compares the running balances with the sums.

## Events

Each posted entry is published to the ledger-events topic. The event holds the entry id, the accounts, the amount, the currency, the reference and the posting time. Consumers are the reporting jobs, the notification service and the finance team's export. Events of one account are published in order.

## Capacity

| Measure | Value at start | Dimensioned for |
|---|---|---|
| entries per day | 1.1 million | 5 million |
| entries per second at peak | 60 | 300 |
| accounts | 2.4 million | 8 million |

| Operation | Median | 95th percentile |
|---|---|---|
| post an entry | 22 ms | 60 ms |
| read an entry | 8 ms | 20 ms |
| read a balance | 6 ms | 15 ms |
| list entries (page of 100) | 30 ms | 75 ms |
| reversal | 28 ms | 70 ms |

## Month-end

On the last working day of the month the finance team closes the period. The close runs these steps in order: the ledger stops accepting entries dated in the closing period, the nightly check runs, the reporting jobs produce the trial balance, and the finance team signs the result. Entries for the closed period are booked in the next period with a reference to the original date.

## Migration from the old module

| Step | Content | Check |
|---|---|---|
| 1 | copy the chart of accounts | numbers equal |
| 2 | copy opening balances | sums equal per class |
| 3 | post in parallel for one month | daily comparison of balances |
| 4 | switch readers to the new service | reports equal |
| 5 | archive the old tables | none |

## Glossary

- **Debit** and **credit**: the two sides of an entry.
- **Posting**: writing an entry to the ledger.
- **Reversal**: a new entry that cancels the effect of an earlier one.
- **Trial balance**: the list of all account balances at a date.
- **Period**: a month for which the books are closed.

## Questions of the finance team

**Can an entry be deleted?** No. A mistake is reversed and the right entry is posted.

**Why does the balance of a merchant payable change after a refund?** A refund is posted as a debit of the merchant payable and a credit of funds at acquirers.

**Which time zone has the posting time?** UTC; the reports convert to the time zone of the reader.

**Can two entries have the same reference?** Yes; a business event can need several entries.

# Appendix 1: related system, KYC Service; reference material for the verification flow

## Case model

A verification case follows one customer through the identity check. A customer can have several cases over time, for example after a change of name, but only one case can be open at once.

| Field | Meaning | Example |
|---|---|---|
| id | identifier of the case | case_7710 |
| customer_id | the customer the case belongs to | cus_30481 |
| status | open, submitted, approved, rejected, needs_review | submitted |
| risk_level | unknown, low, medium, high | low |
| created_at | time the case was opened, UTC | 2026-02-03T08:40:12Z |
| updated_at | time of the last change, UTC | 2026-02-03T08:47:55Z |

### Status changes

| From | To | Trigger |
|---|---|---|
| open | submitted | the customer gives consent and the case is sent to the vendor |
| submitted | approved | the vendor reports a match with low or medium risk |
| submitted | rejected | the vendor reports a mismatch |
| submitted | needs_review | the vendor does not answer in five minutes, or reports an unclear result |
| needs_review | approved | an analyst accepts the case |
| needs_review | rejected | an analyst rejects the case |

A case in `approved` or `rejected` is closed. A new check needs a new case.

## What the customer enters

The customer enters the full name, the date of birth and the country of residence, and photographs one identity document. The supported documents depend on the country.

| Country group | Accepted documents |
|---|---|
| EU and EEA | passport, national identity card, driving licence |
| United Kingdom | passport, driving licence |
| Other | passport only |

For documents with two sides, such as identity cards, the customer photographs both sides, and the app uploads them as two documents of the same case. The app helps with the photograph: it shows an outline, checks the sharpness and the brightness, and asks for a new picture if the text cannot be read.

## The vendor exchange

When a case is submitted, the orchestrator sends the vendor the data of the customer and the references of the images. The vendor answers asynchronously through a callback. The callback carries the vendor request id, the result (`match`, `mismatch`, `unclear`) and a risk level suggested by the vendor.

The orchestrator maps the result to a status. A `match` with the risk level `low` or `medium` becomes `approved`; a `match` with the risk level `high` becomes `needs_review`; a `mismatch` becomes `rejected`; an `unclear` result becomes `needs_review`. The vendor sends each answer at most once, but the orchestrator ignores a second answer for the same request id.

## The review queue

Cases in `needs_review` appear in the queue of the analysts. The queue is sorted by age, oldest first. An analyst opens a case, sees the data of the customer and the images, and decides to accept or reject. The decision needs a short comment. The target is that no case waits longer than four working hours.

| Week | Cases in review (average) | Share of all cases |
|---|---|---|
| pilot week 1 | 41 | 7.8 percent |
| pilot week 2 | 36 | 6.4 percent |
| pilot week 3 | 29 | 5.1 percent |
| pilot week 4 | 27 | 4.7 percent |

The share fell because the app now rejects pictures that are too dark before the upload, which removed many unclear results.

## Capacity

The service handles about 2,400 new cases per day at the start and is dimensioned for 10,000. A case produces on average 2.3 images of about 1.4 MB each.

| Operation | Median | 95th percentile |
|---|---|---|
| open a case | 70 ms | 160 ms |
| upload an image | 380 ms | 900 ms |
| read a case | 25 ms | 60 ms |
| submit | 150 ms | 340 ms |
| list cases (page of 20) | 45 ms | 110 ms |

The vendor needs 40 seconds at the median and 3 minutes at the 95th percentile to answer.

## Localization

The app is available in eleven languages. The error messages of the service are codes, and the app translates them. The names of countries use the ISO 3166 two-letter codes; the app shows the local names. Dates of birth are sent as `YYYY-MM-DD` and shown in the format of the phone.

## Release plan

| App release | Service change |
|---|---|
| 5.0 | read endpoints and case status screen |
| 5.1 | opening cases and uploading documents, ten percent of new customers |
| 5.2 | all new customers |
| 5.3 | customers with an existing case in the old platform |

## Glossary

- **Case**: one run of the identity check for one customer.
- **Vendor**: the external company that compares the document and the data.
- **Analyst**: a member of the operations team who reviews cases.
- **Risk level**: the estimate of the vendor how likely the identity is false.
- **Needs review**: a case that a person has to decide.

## Questions of the app team

**Can the customer change the name after the case is submitted?** No. The case has to be rejected or finished first.

**How many pictures can a case have?** Up to six.

**What does the app show for `needs_review`?** A neutral message that the check takes longer than usual.

**Can the customer start a second case while one is open?** No, the service answers `case_already_open`.
