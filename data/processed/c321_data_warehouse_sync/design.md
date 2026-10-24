DWH-87: Data Warehouse Sync, nightly extracts for the analytics vendor

Type: Story
Priority: Medium
Component: Data Engineering
Reporter: analytics lead
Assignee: data platform team

DESCRIPTION

As the analytics lead, I want the tables that the analytics vendor needs to be copied every night into a staging bucket, so that the vendor can load them into their warehouse without anyone sending files by hand.

SCOPE

Components: sync-job, analytics read replica (PostgreSQL), staging bucket (S3), Analytics vendor.

Flow: sync-job reads the selected tables from the analytics read replica, writes one extract file per table to the staging bucket, and the Analytics vendor downloads the files from the bucket.

Infrastructure (Terraform): warehouse_key, staging_bucket, analytics_replica, analytics_sg, sync_audit, sync_job_policy.

ACCEPTANCE CRITERIA

Functional

AC-1. The job runs every night at 03:00 and finishes within 30 minutes for the current set of tables.
AC-2. One extract file per table is written under a temporary name and renamed when complete.
AC-3. A failed run writes nothing and leaves the previous files in place.
AC-4. A run that fails raises an alert to the data engineering channel.
AC-5. The analytics read replica (PostgreSQL) is a read-only copy of the production database that the sync-job queries for the extracts.

Security

AC-6. Rotation of the database passwords is avoided, because every rotation needs a restart of the job.
AC-7. Data at rest is encrypted with KMS-managed keys.
AC-8. Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.
AC-9. Access tokens expire within 15 minutes; refresh tokens are rotated on use.
AC-10. Traffic between services, and from services to data stores, is encrypted in transit.
AC-11. Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.

Reading centralized logs requires authorization, and only approved staff have it.
AC-12. Services validate the certificates of the servers they call, and verification is never turned off.
AC-13. Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.
AC-14. Runtime secrets are read from the secret store when the service starts.
AC-15. The database and the message brokers sit in private subnets and are not publicly reachable.

Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year.
AC-16. The staging bucket blocks public access and is private by default.
AC-17. Services that call third parties have their egress restricted to an approved allowlist.
AC-18. Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.
AC-19. Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.

Administrative and debug endpoints must not be reachable from the public internet.
Personal data in our databases and object storage is encrypted at rest with AES-256, using keys held in the corporate key management service.
AC-20. Only synthetic data is present outside production.
AC-21. Every webhook we send or receive is signed with an HMAC, and the receiver checks the signature together with the timestamp.
AC-22. User input reaches the database only as query parameters, never as part of the query text.
AC-23. Every build scans libraries and container images, and critical vulnerabilities get a 14-day fix deadline.
AC-24. The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only.

DEFINITION OF DONE

- All acceptance criteria verified in staging with a copy of the table set.
- Dashboard with run duration, number of rows per table and the age of the newest file in the bucket.
- Runbook entry for a failed run (see page "DWH operations", link not valid after the wiki move).

OUT OF SCOPE

- Loading into the vendor's warehouse (owned by the vendor).
- Real-time replication (DWH-101).
- Column-level masking (DWH-110).

# Reference material for the warehouse sync

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

# Appendix 2: related system, Notification Service; reference material for notifications

## Message model

A notification is one message to one recipient over one channel. It is created from an event or by a direct call, rendered from a template and handed to the provider.

| Field | Meaning | Example |
|---|---|---|
| id | identifier of the notification | ntf_90417 |
| channel | email, sms or push | sms |
| recipient_id | the customer or merchant who receives it | cus_30481 |
| template_id | the template that was used | tpl_transfer_received |
| locale | language and region of the message | de-DE |
| status | queued, sent, delivered, failed | delivered |
| created_at | creation time, UTC | 2026-04-02T07:02:11Z |

### Status changes

| From | To | Trigger |
|---|---|---|
| queued | sent | the provider accepts the message |
| sent | delivered | the provider reports delivery |
| queued | failed | the retries are used up |
| sent | failed | the provider reports a permanent failure |

## Templates

Templates are plain text with placeholders in double curly braces. A template has a subject (for email and push) and a body. For every template there is one version per locale. The English version is the fallback.

| Template | Event | Channels |
|---|---|---|
| tpl_transfer_received | wallet.transfer_in | push, sms |
| tpl_payment_declined | payment.declined | email |
| tpl_refund_issued | payment.refunded | email |
| tpl_statement_ready | statement.created | email |
| tpl_topup_failed | wallet.topup_failed | push |

Placeholders are filled from the event: the amount, the currency, the name of the merchant, the date. The notifier formats amounts and dates according to the locale of the recipient. For example, the amount 1234.50 EUR is shown as `1.234,50 €` for `de-DE` and as `€1,234.50` for `en-IE`.

### Template changes

A template is changed through the template endpoint. The change is valid for new messages immediately. The previous version stays in the history, so that the team can see which text a customer received at a given time.

## Choosing the channel

The channel comes from the event type and the preference of the recipient. Each event type has a default channel and a list of allowed channels. The preference of the customer may select any allowed channel. If the chosen channel fails permanently, the notifier does not switch to another channel; the status is `failed` and the producing team decides whether to send again.

## Merging

Messages to the same recipient for the same event type within one minute are merged into one. The merged message uses the template of the event type and lists the amounts one under another. The merge window is a configuration value per event type; transfers use 60 seconds, statements use none.

## Delivery numbers from the pilot

| Channel | Messages | Delivered within 1 minute | Failed |
|---|---|---|---|
| push | 412,000 | 97.2 percent | 0.4 percent |
| sms | 188,000 | 95.1 percent | 1.1 percent |
| email | 305,000 | 91.8 percent | 0.9 percent |

Email deliveries are slower because the providers of the recipients queue messages. The team does not count an email as late if it is delivered within ten minutes.

## Capacity

The notifier processes about 600 thousand messages per day at the start and is dimensioned for 3 million. Peaks occur at 08:00 and 18:00 local time, when scheduled messages are sent.

| Operation | Median | 95th percentile |
|---|---|---|
| render a message | 4 ms | 11 ms |
| hand over to the provider | 120 ms | 450 ms |
| read a status | 9 ms | 24 ms |
| replace a template | 18 ms | 40 ms |

## Migration of the old modules

| Module | Event types | Step | Parallel run |
|---|---|---|---|
| payments | payment.declined, payment.refunded | 1 | two weeks |
| wallet | wallet.transfer_in, wallet.topup_failed | 2 | two weeks |
| statements | statement.created | 3 | two weeks |
| reminders | reminder.due | 4 | two weeks |

During the parallel run the old module also sends. A comparison job lists messages that were sent by one side only.

## Glossary

- **Channel**: the way a message reaches the recipient.
- **Template**: the text of a message with placeholders.
- **Placeholder**: a field in double braces that the notifier fills.
- **Locale**: the combination of language and region.
- **Merge window**: the time within which similar messages are combined.

## Questions of the producing teams

**How do I add a new event type?** Register it with the platform team together with the template for each channel and locale.

**Can I send a message without an event?** Yes, through the notification endpoint.

**What is the maximum length of an SMS?** 160 characters for one part; longer messages are split into parts of 153 characters.

**What if the template is missing for the locale?** The English template is used and the fallback is recorded.
