# Merchant Portal API Design

## Part A (Arjun, platform side)

### 1. Overview

The Merchant Portal API lets merchants see settlements, manage their users and request reports. It sits behind the Portal Gateway and serves the Merchant web app.

### 2. Components

- Portal Gateway: single ingress for the web app.
- Keycloak: identity provider for merchant users; the gateway uses it to check callers.
- portal-backend: settlements, users, reports.
- portal-db (PostgreSQL): settlements, merchant users and report jobs.

### 3. API

- GET /v1/settlements lists settlements, filterable by status.
- GET /v1/settlements/{settlementId} returns id, period, gross, fees and net.
- POST /v1/users invites a user (email, role) and returns id, email and role.
- PATCH /v1/users/{userId}/role changes a role.
- POST /v1/reports requests a report (report_type, from_date, to_date) and returns a job with id, status and expires_at.
- GET /v1/reports/{reportId}/download downloads a finished report.

The service exposes only the endpoints listed in the API section. All traffic is served over HTTPS only.

### 4. Security (platform view)

External API calls are authenticated with OAuth2/OIDC bearer tokens issued by our identity provider. Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it. Production access rights are reviewed every quarter.

All external traffic must use TLS 1.2 or higher.
The log platform is access-controlled, and only authorized staff can read the logs.

Stored PII is protected with AES-256 encryption or stronger. Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.

Internal services trust each other because of the cluster network they sit in, and internal calls carry no credentials.

No secrets are kept in source code, config files, API specs or infrastructure definitions.

portal-db and the message brokers sit in private subnets and are not publicly reachable.

### 5. Deployment

portal-backend runs as three replicas behind the internal load balancer. Rolling updates replace one replica at a time.

---

## Part B (Mei, backend side)

#### reports and queries

The backend (portal-backend, I also say "the portal service") builds reports in a worker. A job goes requested, running, ready. Only one job per type and range runs at a time per merchant. For the filtered lists and the report queries, dynamic queries are assembled with string formatting because the ORM is too slow. We measured it on the settlement list and the difference was big.

#### logging

- Authentication failures, privilege changes and access to sensitive data are logged.

#### data

| area | rule |
|---|---|
| minimization | The portal collects and stores only the personal data needed to run merchant accounts. |
| third parties | Before personal data is shared with a third party, an approved DPA must be in place, and we send just the fields needed. |
| exports | Each export file is encrypted at rest, readable only by the authorized requester, and removed automatically after 72 hours.

#### input and build

All external input is validated against a schema, and invalid requests are rejected.

#### behavior

The invite call creates the user in a pending state and sends an activation email through the notification platform. A role change takes effect on the next token refresh. The settlements list is read from a table filled nightly by the finance pipeline, and the portal never writes to it. Download streams the file.

##### Differences between the halves

Part A says three replicas, Part B says two. Part A names the service portal-backend, Part B sometimes says "the portal service". Part A says the gateway checks callers with Keycloak, Part B has an old note that says the backend does it itself (the old note is outdated). To be cleaned up before review.

# Reference material for the merchant portal

## Settlement model

A settlement is the payout to a merchant for a period. The finance pipeline creates settlements; the portal only reads them.

| Field | Meaning | Example |
|---|---|---|
| id | identifier of the settlement | stl_2026_03_0418 |
| period | the days the settlement covers | 2026-03-01 to 2026-03-07 |
| gross | sum of captured payments in minor units | 4821900 |
| fees | fees taken by Meridian Pay in minor units | 62700 |
| net | gross minus fees | 4759200 |
| currency | ISO 4217 code | EUR |
| status | open, closed, paid | paid |

### Settlement periods

Merchants choose a settlement period when they sign up: daily, weekly or monthly. The period ends at midnight UTC. A settlement is `open` while the period runs, `closed` after the finance pipeline has computed it, and `paid` after the payout has left the bank.

| Period | Closing | Payout |
|---|---|---|
| daily | next morning | two working days after closing |
| weekly | Monday morning | two working days after closing |
| monthly | first working day | three working days after closing |

## Reports

Merchants request reports of three types.

| Report type | Content | Typical size |
|---|---|---|
| transactions | one row per payment in the range | 20 thousand rows |
| settlements | one row per settlement in the range | 60 rows |
| fees | fees by type and day | 400 rows |

A report covers at most thirteen months. Reports are created in the background; the portal shows `pending` until the file is ready. The file is a CSV with a header line. Amounts in the file are written with a decimal point and two decimals, and dates use the format `YYYY-MM-DD`. Merchants can ask for the semicolon as the separator.

### Scheduled reports

A merchant can schedule a report to run every week or every month. The scheduled report uses a moving date range: "last month" always means the previous calendar month. The result appears in the list of reports and an email with a link is sent to the person who scheduled it.

## Team area

A merchant account has a list of people who use the portal. The team area lists them with the email address and a status: `invited`, `active` or `removed`. A new person is added by sending an invitation to an email address; the status is `invited` until the person has accepted. People who leave the merchant are marked `removed` and disappear from the default view, but stay in the list when the filter "all" is chosen.

## The web app

The Merchant web app has four areas: the dashboard with the last settlements and a chart of volume per day, the settlements list, the reports area and the team area. The dashboard chart shows the last 30 days and the same days of the previous month for comparison.

### Filters of the settlements list

| Filter | Values |
|---|---|
| status | open, closed, paid |
| period | a date range |
| currency | the currencies of the account |

## Capacity

The portal has about 38 thousand merchant accounts at the start. On a normal working day 6,500 merchants log in; on Mondays, when weekly settlements close, up to 14,000.

| Operation | Median | 95th percentile |
|---|---|---|
| list settlements (page of 20) | 55 ms | 140 ms |
| read a settlement | 20 ms | 50 ms |
| send an invitation | 90 ms | 210 ms |
| request a report | 60 ms | 130 ms |
| generate a transactions report (20 thousand rows) | 14 s | 31 s |

## Release plan

| Release | Content | Merchants |
|---|---|---|
| 1 | settlements and users | pilot group of ten |
| 2 | reports | pilot group, then 25 percent |
| 3 | scheduled reports | 25 percent, then all |
| 4 | dashboard chart | all |

## Glossary

- **Gross**: the sum of all captured payments in the period.
- **Net**: gross minus fees.
- **Settlement**: the payout for a period.
- **Report**: a file with the data of a period.
- **Invitation**: the email that adds a person to the team area.

## Questions of merchants

**Why does my settlement not include yesterday's payments?** Settlements are computed after the period closes; yesterday's payments are in the open settlement.

**Can I change the settlement period?** Yes, through support; the change applies from the next period.

**Why is a report still pending?** Large reports take a few minutes; the status changes to ready when the file is complete.

**How many people can the team area list?** Fifty.

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
