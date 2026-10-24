# Wallet Service Design

## Part A (Arjun, platform side)

### 1. Overview

The Wallet Service keeps the balance of each customer wallet and lets customers top up and send money to other wallets. The mobile application reaches it only through the Mobile API Gateway.

### 2. Components

- Mobile API Gateway: single ingress for mobile traffic.
- Keycloak: identity provider for customers; the gateway asks it to validate every token.
- wallet-core: balances, top-ups, transfers and profile.
- wallet-db (PostgreSQL): balances, transactions and owner profile.

### 3. Data flow

The mobile app sends wallet and transfer requests to the gateway. The gateway asks Keycloak for token validation and then forwards authenticated requests to wallet-core. wallet-core reads and writes balances and transactions in wallet-db. There is no other path to the database.

### 4. API

- GET /v1/wallets/{walletId} returns id, owner_name, balance and currency.
- POST /v1/wallets/{walletId}/topups takes amount and funding_source_id and returns a transaction (id, type, amount, created_at).
- POST /v1/transfers takes from_wallet_id, to_wallet_id, amount and note and returns a transaction.
- GET /v1/wallets/{walletId}/transactions lists transactions.
- PATCH /v1/wallets/{walletId}/profile changes owner_name, phone_number or address.

### 5. Security (platform view)

The API authenticates callers with JWT bearer tokens. All traffic is served over HTTPS only.

 ⟦S:AUTHZ-04|The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.⟧

⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧ ⟦S:CRYPTO-05|Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.⟧

⟦S:NET-05|Public API traffic passes through a web application firewall with rate limits.⟧

⟦S:CRYPTO-04|Traffic between services, and from services to data stores, is encrypted in transit.⟧

⟦S:AUTHZ-03|Each service must use its own database account with the minimum grants and no shared administrative credentials.⟧

⟦S:AUTH-02|Service-to-service calls are authenticated, either with mutual TLS between the workloads or with a signed workload identity token.⟧

⟦S:SECRET-01|Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.⟧ ⟦S:SECRET-02|On boot, the service pulls its credentials from the approved secret store.⟧

### 6. Deployment

wallet-core runs as three replicas behind the internal load balancer. Rolling updates replace one replica at a time.

---

## Part B (Mei, backend side)

#### What the wallet "core" does

The core (that is wallet-core, sometimes I say the wallet service) does the money maths. For a transfer it first reserves the money on the sender, then credits the receiver, then confirms. ⟦F2|wallet-core takes the list and search parameters of the transaction calls and turns them into the lookups it needs.⟧ If something crashes in the middle a recovery job finishes or cancels the transfer. Core runs as two replicas in our setup (the platform half says three, we should align).

#### Logging

⟦F4|Privilege changes are made by administrators directly in the database and leave no trace.⟧ ⟦S:LOG-02|Logs carry opaque identifiers only and never include secrets, card numbers or personal data.⟧

⟦S:OPS-02|Workloads are non-root, and read-only root filesystems are used wherever they can be.⟧

#### Passwords and login

Customers log in through Keycloak. About password storage in the legacy import: ⟦F1|a fast hash with a single global salt is used for passwords.⟧ We kept that from the old system so migrated customers can still log in without a reset.

#### Browser access

The web wallet calls the gateway from the browser. ⟦F3|Allowed origins are not configured; the gateway reflects the request origin.⟧ This made the web team's life easier during development.

#### Data handling

| topic | rule |
|---|---|
| retention | ⟦S:DATA-02|Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.⟧ |
| third parties | ⟦F5|Customer data is already shared with a new provider while the contract with them is still being negotiated.⟧ |
| input | ⟦S:API-01|Schema validation runs on every external input, and invalid data never reaches the business logic.⟧

**Rate limits**

#### Pipeline

⟦S:OPS-01|CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧

#### Behavior notes

A top-up starts as pending and becomes completed when the funding source confirms it, or failed when it is rejected. A transfer reference makes the call idempotent: the same reference sent twice returns the first transaction. Profile changes apply immediately. The transactions list is newest first and pages with a token.

##### Differences between the halves

Part A says the gateway forwards to three replicas, Part B says two. Part A calls the database "wallet-db", Part B sometimes says "the ledger db" (it is the same database, there is no separate ledger). To be cleaned up before review.

# Reference material for the wallet

## Wallet model in detail

A wallet belongs to one customer and has one currency. A customer can have one wallet per currency. The wallet holds a balance, which is the sum of all booked transactions, and an available balance, which is the balance minus the amounts of pending top-ups that are not yet confirmed and of transfers that are being booked.

| Field | Meaning | Example |
|---|---|---|
| id | identifier of the wallet | wal_5521 |
| owner_name | name of the wallet owner | Alma Berg |
| balance | booked balance in minor units | 12850 |
| currency | ISO 4217 code | EUR |
| status | active or closed | active |
| created_at | creation time in UTC | 2025-11-02T10:14:00Z |

### Transaction types

| Type | Direction | Created by |
|---|---|---|
| topup | in | a confirmed top-up from a funding source |
| transfer_out | out | a transfer to another wallet |
| transfer_in | in | a transfer from another wallet |
| fee | out | a fee of a product, for example a faster payout |
| correction | in or out | the operations team, with a reason |

Every transaction carries an id, the type, the amount, the currency, the time of booking and a reference text of at most 140 characters. Transactions are never changed after booking. A mistake is corrected by a new transaction of the type `correction`.

## Top-ups

A top-up moves money from a funding source of the customer to the wallet. The customer chooses the funding source in the app. The request arrives with the amount and the identifier of the funding source. The service creates a transaction in the status `pending` and asks the funding provider to collect the money. When the provider confirms, the transaction becomes `booked` and the available balance increases. When the provider refuses, the transaction becomes `failed` and nothing changes in the balance.

The limits of a top-up depend on the level of the wallet.

| Wallet level | Minimum | Maximum per top-up | Maximum per month |
|---|---|---|---|
| basic | 5.00 EUR | 500.00 EUR | 2,000.00 EUR |
| standard | 5.00 EUR | 2,500.00 EUR | 10,000.00 EUR |
| premium | 5.00 EUR | 10,000.00 EUR | 40,000.00 EUR |

A top-up that would break a limit is refused with the answer `limit_exceeded` and the name of the limit.

## Transfers

A transfer moves money from one wallet to another wallet in the same currency. The sender chooses the receiver by phone number or by the name of the receiver, and the app resolves the choice to a wallet id before it sends the request. The note of the transfer is shown to both sides.

Rules of a transfer:

1. Both wallets must be `active`.
2. The amount must be at least 0.01 and at most the available balance of the sender.
3. The currencies of both wallets must be equal.
4. The sender and the receiver must be different wallets.
5. Both balances change in one database transaction.

Failures have their own answers: `wallet_closed`, `insufficient_funds`, `currency_mismatch` and `same_wallet`.

### Examples

A customer with 40.00 EUR sends 15.50 EUR to a friend. After the transfer the sender has 24.50 EUR and the friend has 15.50 EUR more. Both see a transaction with the note, the sender as `transfer_out` and the friend as `transfer_in`.

A customer with 10.00 EUR tries to send 12.00 EUR. The service answers `insufficient_funds` and the app shows the missing amount of 2.00 EUR with a button that opens the top-up screen.

## Profile data

The profile holds the name of the owner, the phone number and the address. A change of the name is visible in new transfers immediately; old transactions keep the name that was valid at the time. The phone number must be in international format and unique among the wallets, because it is the way friends find each other. The address has the fields street, number, postal code, city and country.

## The mobile app screens

The app has five screens that use the service.

- **Home** shows the balance, the last five transactions and the buttons for top-up and send.
- **Top-up** shows the funding sources and the amount field with the limit of the wallet level.
- **Send** shows the contact search, the amount, the note field and a summary before the customer confirms.
- **History** shows all transactions in pages of 50, newest first, with a filter for the type.
- **Profile** shows the owner data and lets the customer change the name, the phone number and the address.

## Capacity

The wallet serves 1.8 million customers at the start and is dimensioned for 4 million in two years. On a normal day the service books 90 thousand transactions, on the last day of the month up to 350 thousand.

| Operation | Median | 95th percentile |
|---|---|---|
| read wallet | 15 ms | 40 ms |
| list transactions (page of 50) | 38 ms | 95 ms |
| transfer | 85 ms | 210 ms |
| top-up request | 120 ms | 300 ms |
| profile change | 30 ms | 80 ms |

## Reconciliation job

Every night at 02:00 UTC the reconciliation job computes, for every wallet, the sum of its transactions and compares it with the stored balance. Differences are written into a table that the finance team reads in the morning. In the first month of the pilot, 3 of 1.8 million wallets showed a difference; all were caused by a manual correction that had been entered twice and was reversed.

## Release plan

| App release | Wallet service change | Share of customers |
|---|---|---|
| 4.1 | read endpoints | 100 percent |
| 4.2 | top-ups and transfers | 10 percent, then 100 percent |
| 4.3 | profile changes | 100 percent |
| 4.4 | transaction filters | 100 percent |

## Glossary

- **Available balance**: balance minus pending amounts.
- **Funding source**: a bank account or a card from which a customer tops up.
- **Minor unit**: the smallest unit of the currency, for example the cent.
- **Reference**: free text that a customer adds to a transfer.
- **Correction**: a booking by the operations team that fixes an earlier booking.

## Questions of the app teams

**Why is my balance different from the available balance?** Pending top-ups and transfers in progress are not counted in the available balance.

**Can a closed wallet receive money?** No; a transfer to a closed wallet is refused with `wallet_closed`.

**Are transactions sorted by booking time?** Yes, newest first; transactions with the same time are sorted by id.

**How long does a top-up take?** Usually a few seconds; some funding sources need up to two working days and the transaction stays `pending` meanwhile.

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

# Appendix 2: related system, Ledger Service; reference material for the ledger

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
