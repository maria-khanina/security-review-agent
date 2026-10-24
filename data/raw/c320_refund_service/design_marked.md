# Refund Service: Architecture and Control Catalogue

Author: Anja K., Security Champion, Payments
Revision: 3 (revision 2 and the older "return handler" page are still linked from the wiki and partly outdated)
Review: Security Architecture

## 1. Summary

The Refund Service accepts requests to return money to a customer's card, validates them against the original payment, keeps the state of each refund and publishes status events. Merchants and support agents use it. Because it touches payments, the service is reviewed as part of the PCI scope. This document describes the architecture and then catalogues the security controls with identifiers that match the compliance tracker. The tracker holds the implementation status; the catalogue lists only what the design commits to.

## 2. Architecture

Merchant backends and support agents send refund requests to Refunds Gateway, which forwards authenticated requests to refund-core. refund-core applies the refund rules and stores each refund in refund-db (PostgreSQL), together with the reference of the original payment. Every change of state is published to refund-events (Kafka), which the ledger and the notification service consume.

The API has five operations under /v1:

- POST /v1/refunds creates a refund from payment_id, amount, currency, reason and requested_by and returns id, payment_id, status, amount and currency.
- GET /v1/refunds/{refundId} returns one refund.
- GET /v1/refunds lists refunds and can be filtered by status and payment_id.
- POST /v1/refunds/{refundId}/approval approves or rejects a refund (decision, comment).
- POST /v1/refunds/{refundId}/cancellation cancels a pending refund (reason).

## 3. Refund rules

The sum of the refunds of a payment may not exceed the amount of the payment. A refund is pending until it is approved; refunds below the automatic limit are approved on creation. A refund can be cancelled while pending. After approval the money is returned through the acquirer connector of the payment service, and the refund becomes completed or failed. Failed refunds are reviewed by the payments operations team.

## 4. Control catalogue

Identifiers (R-1 and so on) match the compliance tracker. The "return handler" page used a different numbering and should not be used.

### 4.1 Identity and access

- R-1: ⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧
- R-2: ⟦F2|refund-core receives each request from Refunds Gateway together with the identity of the calling client or agent.⟧
- R-3: ⟦S:AUTHZ-01|Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.⟧
- R-4: ⟦S:AUTHZ-04|Nothing administrative or meant for debugging can be called from outside our network.⟧
- R-5: ⟦S:AUTHZ-05|Production access rights are reviewed every quarter.⟧

### 4.2 Data and cryptography

- R-6: ⟦F1|The full card number is kept with the payment record and returned in the API response, so that merchants can reconcile refunds against their own books.⟧
- R-7: ⟦S:CRYPTO-01|Stored PII is protected with AES-256 encryption or stronger.⟧
- R-8: ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
- R-9: ⟦S:DATA-01|Only the personal data needed for the purpose is collected and stored.⟧
- R-10: ⟦S:DATA-03|Third parties receive only the fields they need, and only if an approved data processing agreement covers them.⟧
- R-11: ⟦S:DATA-05|Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.⟧

⟦S:CRYPTO-03|All public-facing endpoints terminate TLS 1.2 or higher.⟧
⟦S:LOG-04|The log platform is access-controlled, and only authorized staff can read the logs.⟧

⟦S:AUTH-02|We do not trust the internal network by itself: every internal call is authenticated with mTLS or workload identity tokens.⟧

### 4.3 Transport, secrets and network

- R-12: All traffic is served over HTTPS only.
- R-13: ⟦S:SECRET-01|Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.⟧

⟦S:SECRET-02|Runtime secrets must be fetched from the approved secret store at startup.⟧
- R-14: ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧

### 4.4 Logging and application security

- R-15: ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are written to the logs.⟧
- R-16: ⟦S:API-01|Schema validation runs on every external input, and invalid data never reaches the business logic.⟧
- R-17: ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧

## 5. Deployment and capacity

refund-core is stateless and runs as three replicas behind the internal load balancer (revision 2 said two). Refunds Gateway is the only component with a public address. The peak is around forty refund requests a second during sale events; the database is sized for ten times that. refund-events has three partitions keyed by payment_id so that the events of one payment stay in order.

## 6. Observability

One dashboard per environment shows requests, refund states and the age of the oldest pending refund. An alert fires when a refund is pending longer than the threshold in the runbook. The payments on-call rota receives the alerts. The runbook is in the payments space (the link to the old space may not work).

## 7. Known gaps

The catalogue has no implementation status column; the tracker carries it. The retention period for completed refund records is not decided. The sections of revision 1 about manual refunds by e-mail are kept in the archive and are not repeated here.

# Reference material for refunds

## Refund model

A refund returns money from a captured payment to the customer. It belongs to exactly one payment and has its own lifecycle.

| Field | Meaning | Example |
|---|---|---|
| id | identifier of the refund | ref_3304 |
| payment_id | the payment that is refunded | pay_0042c9 |
| amount | refunded amount in minor units | 2500 |
| currency | ISO 4217 code | EUR |
| reason | reason code | goods_returned |
| requested_by | the person or system that asked | agent_218 |
| status | requested, approved, rejected, executed, cancelled, failed | executed |
| created_at | time of the request, UTC | 2026-03-18T13:41:55Z |

### Reason codes

| Code | Meaning |
|---|---|
| goods_returned | the customer returned the goods |
| service_not_delivered | the service was not delivered |
| duplicate_payment | the customer paid twice |
| price_adjustment | the merchant lowers the price afterwards |
| goodwill | the merchant refunds without a claim |
| other | free text in the comment field |

## Rules for amounts

- The amount of one refund must be positive and not larger than the captured amount of the payment minus earlier refunds.
- The currency of the refund must be the currency of the payment.
- A refund can be requested up to 180 days after the capture.
- A payment can have at most 20 refunds.

A request that breaks a rule gets the answer `refund_not_allowed` with the name of the rule.

## Statuses

| From | To | Trigger |
|---|---|---|
| requested | approved | the approving person accepts |
| requested | rejected | the approving person refuses |
| requested | cancelled | the requester withdraws the request |
| approved | executed | the payment gateway confirms the refund |
| approved | failed | the confirmation does not arrive after five retries |

`executed`, `rejected`, `cancelled` and `failed` are final. A failed refund is handed to the operations team, which either repeats it by hand or contacts the merchant.

## Timing

The customer sees the money on the card statement after a time that depends on the bank. The gateway confirms the refund within seconds; the bank needs between three and ten working days.

| Step | Typical time |
|---|---|
| request to approval | 4 working hours |
| approval to execution | under 1 minute |
| execution to money on the statement | 3 to 10 working days |

## Volumes

The service handles about 9,000 refund requests per day at the start. About 62 percent of requests come from merchant backends, 38 percent from support agents.

| Reason | Share |
|---|---|
| goods_returned | 47 percent |
| duplicate_payment | 18 percent |
| service_not_delivered | 14 percent |
| price_adjustment | 9 percent |
| goodwill | 7 percent |
| other | 5 percent |

## Capacity

| Operation | Median | 95th percentile |
|---|---|---|
| request a refund | 85 ms | 200 ms |
| read a refund | 14 ms | 35 ms |
| list refunds (page of 50) | 40 ms | 95 ms |
| record a decision | 60 ms | 140 ms |
| cancel | 45 ms | 100 ms |

## Events

Each change of status is published to refund-events with the refund id, the payment id, the old and the new status and the time. The consumers are the ledger, the notification service and the reporting jobs.

## Reports for the finance team

The finance team receives a daily table of refunds by reason, merchant and status, and a weekly table of the refund rate per merchant, which is the share of the captured amount that was refunded. Merchants with a refund rate above five percent are listed for the commercial team.

## Release plan

| Phase | Users | Duration |
|---|---|---|
| 1 | support agents | one month |
| 2 | merchants in groups of fifty | three months |
| 3 | switch-off of the old module | one month after the last group |

## Glossary

- **Refund**: money returned to the customer after a capture.
- **Reason code**: the standard explanation of a refund.
- **Refund rate**: the share of captured money that is refunded.
- **Final status**: a status that never changes again.

## Questions of the merchants

**Can I refund more than the payment?** No, the answer is `refund_not_allowed`.

**Can I cancel an executed refund?** No. A refund that was executed cannot be undone.

**How do I see why a refund failed?** The refund record has a failure reason; the support team can explain it.

**Is a partial refund possible?** Yes, any amount up to the remaining captured amount.

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
