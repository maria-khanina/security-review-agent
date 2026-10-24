# KYC Verification: Product and Design Overview

Owner: Onboarding Product
Status: Approved for build

## 1. Vision

Opening an account should feel like a handshake, not a form. Today, verifying a new customer takes days of back and forth, and a large share of applicants give up before they finish. The KYC Verification Service turns identity checks into a smooth, enterprise-grade, secure-by-design journey: the customer provides their details and a photo of an identity document, we check them with a trusted verification partner, and in most cases the customer is verified within minutes.

Success for the first release means three things: more applicants finish the journey, fewer cases need a human, and every decision can be explained to a regulator in plain language.

## 2. Customer value

- Applicants get a short, clear journey with fast feedback.
- Operations focus on the genuinely difficult cases instead of routine ones.
- Compliance gets a consistent record of each decision and the evidence behind it.
- Growth gets a conversion funnel it can measure and improve.

## 3. Scope

In scope: opening a verification case, uploading identity documents, submitting the case to the verification partner, tracking status and listing cases for operations. Out of scope for now: liveness checks, business (KYB) verification and re-verification campaigns.

## 4. How it works

The customer application talks to kyc-orchestrator. kyc-orchestrator keeps document images in the kyc-documents bucket (S3), keeps case records in kyc-db (PostgreSQL) and hands cases to the Identity verification vendor. The vendor reports the result back, and the service updates the case.

The API has five operations. POST /v1/kyc/cases opens a case from the customer's customer_id, full_name, date_of_birth and country, and returns the case with its id, status, risk_level and customer_id. POST /v1/kyc/cases/{caseId}/documents uploads a document (document_type and content_base64) and returns a receipt with a document_id and the time received. GET /v1/kyc/cases/{caseId} returns the status of one case. POST /v1/kyc/cases/{caseId}/submit sends the case to the partner once the customer has given consent. GET /v1/kyc/cases lists cases for the operations team.

## 5. The customer journey

A case moves through opened, documents received, submitted, and then verified, rejected or manual review. In manual review an operator may ask the customer for another document; the customer sees a friendly message and can upload more. After a rejection, the customer can start again, which opens a new case so that each decision stays attached to the evidence it was based on. The risk level assigned by the partner is shown to operations only.

## 6. Security and compliance posture

Security is a first-class feature of this service, not an afterthought, because customers trust us with their identity. The commitments below are the ones we make to customers and to the compliance team.

- Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS. Access tokens live for at most 15 minutes, and every refresh token is replaced when it is used. The login and token endpoints throttle repeated failures and apply a temporary lockout once an account reaches ten consecutive failed attempts.

Rate limit per client: 60 requests per minute, with HTTP 429 and a Retry-After header once the limit is hit.

Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.
- Every request for a customer-owned case or document verifies that the caller owns the resource or is entitled to it. The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.
- Encryption at rest with AES-256 covers personal data in databases and object storage, and its keys live in the corporate key management service. Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year. TLS certificate verification is enabled in all clients, with no option to disable it. We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.

Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.

The external API sits behind a WAF that also applies rate limiting.

Nothing travels unencrypted inside our network, because service-to-service and service-to-datastore links are encrypted.
- Secrets stay out of the repository: not in code, configuration, specs or infrastructure files. At startup the service fetches its secrets from the approved secret store.

Database credentials are per service with least-privilege grants, and no shared admin account is used by the application.
- kyc-db and the message brokers sit in private subnets and are not publicly reachable. The kyc-documents bucket blocks public access and is private by default. Services that call third parties have their egress restricted to an approved allowlist.
- Authentication failures, privilege changes and access to sensitive data are written to the logs.
- Third parties receive only the fields they need, and only if an approved data processing agreement covers them. Non-production environments contain no real personal or card data.
- All external input is validated against a schema, and invalid requests are rejected. Webhook payloads, inbound and outbound, carry an HMAC signature and a timestamp, and the receiver verifies both. Clients get generic error messages without stack traces, SQL or internal hostnames. Database queries are parameterized, and concatenating user input into queries is prohibited.
- Every build scans libraries and container images, and critical vulnerabilities get a 14-day fix deadline. The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only.

## 7. Rollout

Rollout starts with new customers in one market, behind a flag, with operations watching every manual-review case. After two weeks of clean metrics, the flag opens to all customers in that market. A second market follows once the verification partner confirms its coverage of that market's documents. At each step the team reviews conversion, the manual-review rate and the partner's response times before moving on.

## 8. Open questions

- Which document types ship in the first market? Compliance and the partner are aligning (see the note in the shared drive, link may have moved).
- What wording should the consent screen use? Legal is drafting it.

# Reference material for the verification flow

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

# Appendix 1: related system, Data Warehouse Sync; reference material for the warehouse sync

## Tables in the extract

The nightly sync copies a fixed list of tables. The list is configuration.

| Table | Rows (approx.) | Key column | Change column | Mode |
|---|---|---|---|---|
| payments | 40,000,000 | id | updated_at | incremental |
| refunds | 3,100,000 | id | updated_at | incremental |
| settlements | 1,900,000 | id | updated_at | incremental |
| merchants | 38,000 | id | updated_at | full |
| wallets | 1,800,000 | id | updated_at | incremental |
| transactions | 210,000,000 | id | created_at | incremental |
| currencies | 170 | code | none | full |

In incremental mode the job copies the rows whose change column is later than the latest value of the previous successful run. In full mode it copies the whole table. Small tables use the full mode because it is simpler and fast enough.

## Files

For each table and run the job writes one or more files into the folder of the day.

| Property | Value |
|---|---|
| format | CSV with a header line |
| separator | comma |
| encoding | UTF-8 |
| quoting | double quotes where needed |
| maximum rows per file | 1,000,000 |
| file name | table_name-YYYYMMDD-NNN.csv |

The manifest file `manifest-YYYYMMDD.json` lists the tables, the files, the row counts and the status of each table. The vendor starts loading only when the manifest exists.

### Example manifest

```
{
  "run_date": "2026-03-14",
  "status": "partial",
  "tables": [
    {"name": "payments", "files": 3, "rows": 2310440, "status": "ok"},
    {"name": "refunds", "files": 1, "rows": 41120, "status": "ok"},
    {"name": "transactions", "files": 0, "rows": 0, "status": "failed"}
  ]
}
```

## Timing of a run

| Step | Duration |
|---|---|
| read the configuration | under 1 s |
| payments | 9 min |
| refunds | 1 min |
| settlements | 1 min |
| merchants, currencies | under 1 min |
| wallets | 3 min |
| transactions | 21 min |
| manifest | under 1 s |

A run takes about 36 minutes. The window for the job is one hour, from 02:00 UTC. The vendor loads at 04:00 UTC.

## Growth

The table `transactions` grows by about 1.2 million rows per day. The extract of this table needs about two thirds of the run time. If the growth continues, the table has to be split into two jobs when the run exceeds fifty minutes.

| Quarter | Rows per night (approx.) | Run time |
|---|---|---|
| now | 1.9 million | 36 min |
| +2 | 2.6 million | 45 min |
| +4 | 3.4 million | 55 min |

## Rerun of a day

A failed day can be repeated by hand for the date. The rerun replaces the files of the day and writes a new manifest. Incremental tables return to the position of the last successful run before the rerun date.

## Messages to the analytics team

After each run the job posts a message into the channel of the analytics team: the date, the status, the number of tables, the total number of rows and the run time. For a `partial` run the message lists the failed tables.

## Comparison with the old export

During the two weeks of the parallel run, the vendor compares the files of the old export and the new job table by table: the number of rows, the sum of the amount columns and a checksum of the key columns. The new job is accepted when the comparison shows no differences on ten nights in a row.

| Night | Tables compared | Differences |
|---|---|---|
| 1 | 7 | 2 (time zone of the change column) |
| 2 | 7 | 1 |
| 3 | 7 | 0 |
| 4 | 7 | 0 |
| 5 | 7 | 0 |

## Glossary

- **Extract**: the files with the rows of one table for one run.
- **Manifest**: the file that lists the files and the status of a run.
- **Incremental mode**: copying only rows that changed.
- **Full mode**: copying the whole table.
- **Partial run**: a run in which at least one table failed.

## Questions of the analytics team

**Why is a table missing in the folder of today?** Check the manifest; a failed table is listed there with the status `failed`.

**Can I get a table that is not on the list?** Ask the platform team to add it to the configuration.

**Are deleted rows copied?** No. The extract contains only rows that exist at the time of the run.

**Which time zone do the dates use?** UTC.

# Appendix 2: related system, Wallet Service; reference material for the wallet

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
