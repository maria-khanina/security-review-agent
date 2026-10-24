# Payment Gateway: Architecture and Security Control Catalogue

Author: Rina M., Security Champion, Payments Platform
Review: Security Architecture
Revision: 7 (revision 6 called the front component "Edge-GW"; the name is retired but still appears in two dashboards)

## 1. Summary

The Payment Gateway accepts card payments from merchants, routes them to acquiring banks and publishes payment events. Because it sits on the path of every payment, its controls are catalogued here in detail. Reviewers should read the control catalogue (section 5) first and the architecture afterwards.

## 2. Architecture

Merchant backends call the Payments Edge Gateway with a payment request that carries a card token. The gateway forwards validated requests to payments-core. payments-core stores payment records in payments-db (PostgreSQL), sends authorization requests to the acquirer through the Acquirer connector and publishes status events on payment-events (Kafka).

⟦F1|payments-core is the central service of the gateway: it owns the payment state machine and coordinates the database, the acquirer connector and the event stream.⟧ ⟦F3|payments-core signs and protects the messages it exchanges with the acquirer and with the event stream.⟧

## 3. API

- POST /v1/payments creates a payment (amount, currency, card_token, merchant_id, reference) and returns id, status, amount, currency, last4 and merchant_id.
- GET /v1/payments/{paymentId} returns one payment.
- POST /v1/payments/{paymentId}/capture captures an authorized payment (amount).
- POST /v1/payments/{paymentId}/refunds refunds a payment (amount, reason) and returns id, status and amount.
- GET /v1/payments lists payments.

A payment moves through created, authorized, captured and refunded, or ends in failed after a decline. Creation is idempotent on the reference together with the merchant identifier.

## 4. Reporting

Finance receives settlement reports as files. The reports are produced by a nightly job that writes CSV files to a storage bucket and notifies finance when they are ready.

## 5. Control catalogue

Control identifiers (P-1 and so on) match the compliance spreadsheet (link TBD; the spreadsheet under the previous team name is stale).

### 5.1 Identity and access

- P-1: Callers authenticate with OAuth2 bearer tokens.
- P-3: ⟦S:AUTHZ-04|Admin and debug endpoints are reachable only from the internal network, not from the public internet.⟧
- P-4: ⟦S:AUTHZ-05|A quarterly access review covers all production systems.⟧

⟦F4|Any authenticated caller can read any payment record if it knows the payment identifier.⟧

### 5.2 Data protection

- P-6: ⟦S:CRYPTO-03|All external traffic uses TLS 1.2 or higher.⟧

⟦S:AUTH-01|No external endpoint serves anonymous traffic; callers present an OAuth2 token or a TLS client certificate.⟧
- P-7: ⟦S:DATA-01|The gateway collects and stores only the personal data needed for payment processing.⟧

⟦S:LOG-04|Access to centralized logs must be limited to authorized staff.⟧
- P-9: ⟦S:DATA-03|Personal data goes to third parties only under an approved data processing agreement, and only the required fields are sent.⟧

⟦S:API-01|All external inputs must be validated against a schema and rejected if invalid.⟧
- P-10: ⟦F2|Report files remain in the storage bucket and are never deleted.⟧

### 5.3 Secrets and network

- P-11: ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧
- P-13: ⟦S:NET-01|payments-db and the Kafka brokers sit in private subnets and are not publicly reachable.⟧

### 5.4 Logging

- P-14: ⟦S:LOG-01|The audit trail includes authentication failures, privilege changes and sensitive-data access.⟧

⟦S:SECRET-02|On boot, the service pulls its credentials from the approved secret store.⟧

### 5.5 Application security

- P-17: Requests are validated against strict schemas.
- P-18: ⟦S:API-05|Database queries are parameterized, and user input is never concatenated into SQL.⟧

⟦F5|The internal services call each other with one long-lived token that every service reuses.⟧

### 5.6 Operations

## 6. Capacity and deployment

The gateway handles several hundred authorization requests per second at peak. payments-core is stateless and runs as four replicas behind the internal load balancer (revision 6 said three; four is correct); the database primary is the single writer with a standby in a second availability zone. Deployments are rolling with a small canary for fifteen minutes. The acquirer connector retries failed calls with growing delays and surfaces a failed payment when the acquirer stays unavailable.

## 7. Events

Every state change publishes an event on payment-events with at-least-once delivery. Consumers, for example ledger and notifications, de-duplicate on the payment identifier. Events carry identifiers and amounts and no card data.

## 8. Open items

- Status column of the catalogue: the controls are listed without an implementation status; the spreadsheet carries it (link TBD).
- Acquirer timeout: ten or fifteen seconds is still being agreed with the acquirer (TBD).
- Reference to the architecture of revision 1 lives in the archived wiki and may not open.

# Part 2: Reference material for the payment flows

This second part collects the functional details that the team keeps asking for. It does not change the decisions of the first part.

## 9. Payment lifecycle in detail

A payment passes through a fixed set of statuses. The table shows every allowed change and what triggers it.

| From | To | Trigger |
|---|---|---|
| (new) | authorized | the acquirer approves the amount |
| (new) | declined | the acquirer refuses the amount |
| (new) | pending | the acquirer does not answer within three seconds |
| pending | authorized | a late approval arrives |
| pending | declined | the retries are used up |
| authorized | captured | the merchant captures the full or a partial amount |
| authorized | expired | seven days pass without a capture |
| captured | partially_refunded | a refund smaller than the captured amount is booked |
| captured | refunded | refunds add up to the captured amount |
| partially_refunded | refunded | the remaining amount is refunded |

No other change is allowed. A request that asks for a change outside the table gets the answer `invalid_state` and nothing is stored. The status `expired` is final. When a merchant captures a payment after it has expired, the answer is `invalid_state`, and the merchant has to create a new payment.

### Partial captures

A merchant may capture less than the authorized amount. The difference is released after the capture, so the customer sees only the captured amount on the statement. A second capture on the same payment is not possible in the first release. Merchants that ship an order in several parcels ask for it often; the product team has it on the list for the next release.

Example: a payment of 120.00 EUR is authorized. The merchant ships the first parcel and captures 80.00 EUR. The payment is `captured` with the captured amount 80.00 EUR, and the remaining 40.00 EUR is released. If the customer then returns an item worth 25.00 EUR, the merchant requests a refund of 25.00 EUR, and the payment becomes `partially_refunded`.

## 10. Amounts and currencies

Amounts are whole numbers in the smallest unit of the currency. The number of decimals depends on the currency.

| Currency | Decimals | Example | Stored value |
|---|---|---|---|
| EUR | 2 | 12.34 | 1234 |
| GBP | 2 | 7.05 | 705 |
| SEK | 2 | 99.90 | 9990 |
| JPY | 0 | 1500 | 1500 |
| KWD | 3 | 4.250 | 4250 |

The currency of a payment is the currency of the merchant account. Conversion between currencies is not part of the first release; a merchant with an account in EUR cannot accept GBP. The currency code is always three capital letters according to ISO 4217. A request with a code that is not on the list of supported currencies gets the answer `unsupported_currency`.

Rounding is needed only for fees. The fee of a payment is calculated from the captured amount with the percentage of the merchant plan, rounded half up to the smallest unit, plus the fixed part of the plan. The fee is not part of the payment record; it is calculated again by the settlement module.

## 11. Routing to acquirers

Each merchant account is connected to one primary acquirer and, optionally, one fallback. The Acquirer connector chooses the acquirer by these rules, in this order:

1. If the card scheme of the payment is not supported by the primary acquirer, the fallback is used.
2. If the amount is above the limit of the primary acquirer, the fallback is used.
3. If the primary acquirer answered with a technical error three times in the last minute, the fallback is used for the next five minutes.
4. Otherwise the primary acquirer is used.

The card scheme is derived from the first digits of the card. The connector keeps a small table of ranges that is updated by the operations team once a month. If no range matches, the payment is declined with the reason `scheme_not_supported`.

### Acquirer limits

| Acquirer | Maximum per payment | Maximum per day and merchant |
|---|---|---|
| Acquirer A | 15,000.00 EUR | 250,000.00 EUR |
| Acquirer B | 10,000.00 EUR | 150,000.00 EUR |
| Acquirer C | 5,000.00 EUR | 80,000.00 EUR |

The limits are taken from the contracts and are configuration values, not code. When a limit changes, the operations team updates the configuration, and the change is applied by the connector within a minute.

## 12. The events of the payment-events topic

Every change of a payment is published as an event. All events have the same envelope.

| Field | Type | Example |
|---|---|---|
| event_id | string | evt_8f3a21 |
| event_type | string | payment.captured |
| occurred_at | timestamp | 2026-03-14T09:21:07Z |
| payment_id | string | pay_0042c9 |
| merchant_id | string | mer_1187 |
| status | string | captured |
| amount | integer | 8000 |
| currency | string | EUR |

The event types are `payment.authorized`, `payment.declined`, `payment.captured`, `payment.expired`, `payment.refunded` and `payment.partially_refunded`. Events of one payment are published in order, because the payment id is the key of the Kafka partition. Consumers must expect that an event can be delivered more than once and must use the event id to recognize repeats.

### Consumers

- The ledger service books the movement of money for `captured` and `refunded`.
- The notification service sends messages to merchants for `declined` and `refunded`.
- The reporting jobs read all events once a day and fill the tables of the finance team.

## 13. Reconciliation with the acquirers

Every night the acquirers send a settlement file. The gateway reads the file and compares each line with its own records. A line is matched by the acquirer message id. There are four outcomes: the line matches exactly, the amount differs, the line has no payment on our side, or a payment of ours has no line. The first outcome is the normal one and needs no action. The other three are written into the exception table, and the finance team works through it in the morning.

In the first three months of the pilot, the share of lines that matched exactly was 99.6 percent. Most exceptions came from payments that were captured late in the evening and appeared in the file of the next day. The team added a tolerance of one day for these cases.

## 14. Capacity and performance

The expected volume for the first year is 1.2 million payments per month, with peaks of 40 payments per second on the last Friday of the month. The service is dimensioned for 120 payments per second so that a failed instance does not cause delays.

| Operation | Median | 95th percentile |
|---|---|---|
| create payment | 640 ms | 1,400 ms |
| read payment | 18 ms | 45 ms |
| capture | 410 ms | 900 ms |
| refund | 380 ms | 850 ms |
| list payments (page of 50) | 60 ms | 140 ms |

The long time of the create call is the time of the acquirer. The gateway itself needs about 40 ms. The list call reads from an index on merchant and creation time.

## 15. Test plan

The tests follow the lifecycle table. For each allowed change there is a test that drives the payment into the start status, triggers the change and checks the new status, the stored record and the published event. For each forbidden change there is a test that expects `invalid_state`. A third group of tests uses the acquirer simulator, which can answer with approval, refusal, delay and technical error.

The contract tests compare the answers of the new service with the answers of the monolith for 400 recorded requests. The tests fail on any difference in field names, types or status codes. A short list of known differences is kept in the repository and reviewed in each release.

## 16. Release history and plan

| Version | Content | Date |
|---|---|---|
| 0.1 | create and read | month 1 |
| 0.2 | capture, partial capture | month 2 |
| 0.3 | refunds | month 3 |
| 0.4 | list endpoint, events | month 4 |
| 1.0 | pilot merchants | month 5 |
| 1.1 | all new merchants | month 6 |
| 1.2 | existing merchants in groups | months 7 to 9 |

## 17. Glossary

- **Authorization**: the approval of an amount by the acquirer; it reserves the amount on the card of the customer.
- **Capture**: the instruction to turn an authorization into a claim for money.
- **Refund**: giving money back to the customer after a capture.
- **Acquirer**: the bank that processes the card payments of a merchant.
- **Settlement**: the payout of the captured amounts, less fees, to the merchant.
- **Scheme**: the card network, for example Visa or Mastercard.
- **Minor unit**: the smallest unit of a currency, for example the cent.

## 18. Questions that integrators ask

**Can I capture more than I authorized?** No. The answer is `amount_exceeds_authorization`.

**How long is an authorization valid?** Seven days. After that the payment is `expired`.

**Why is my payment `pending`?** The acquirer did not answer in time. Wait for the event or read the payment again after a minute.

**Can I refund after a partial capture?** Yes, up to the captured amount.

**Do you send the events in order?** For one payment, yes. Events of different payments can overtake each other.

**What happens at the daylight saving change?** All timestamps are in UTC, so nothing happens.

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
