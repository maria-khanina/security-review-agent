# Notification Service: stories and design

Epic: NOTIF-210 (Event-driven notifications)
Status: Ready for development
Related: NOTIF-190 (old mailer retirement, link TBD)

## Overview

The notifier consumes domain events from domain-events (Kafka), renders messages from templates and sends them through the Email and SMS provider. It also exposes an API for manual sends, template management and delivery status.

## Stories

### NOTIF-211: Send on event

As a product team, I want a message to be sent when a domain event arrives so that customers are informed without extra integration.

Acceptance criteria:
- An event on domain-events leads to exactly one notification per recipient.
- The channel follows the customer's preference.
- A failed delivery is retried with increasing delays and finally marked failed.

### NOTIF-212: Manual send and status

As a support agent, I want to send a notification manually and check its status.

Acceptance criteria:
- POST /v1/notifications accepts channel, recipient_id, template_id and locale and returns id, status and channel.
- GET /v1/notifications/{notificationId} returns the same shape.
- GET /v1/notifications lists notifications and can be filtered by channel.

### NOTIF-213: Manage templates

As a product owner, I want to change message wording without a deployment.

Acceptance criteria:
- PUT /v1/templates/{templateId} creates or replaces a template with a subject and a body.
- The newest template version for the recipient's locale is used; English is the fallback.
- A template with an unknown placeholder is rejected.

## Non-functional requirements

The following apply to every story (TBD: repeat as acceptance criteria in each ticket).

| ID | Area | Requirement |
|---|---|---|
| NFR-1 | Service authentication | ⟦S:AUTH-02|Service-to-service calls are authenticated, either with mutual TLS between the workloads or with a signed workload identity token.⟧ |
| NFR-2 | Tokens | ⟦F1|Access tokens stay valid for a week, so the calling services do not have to renew them often.⟧ |
| NFR-4 | Internal transport | ⟦S:CRYPTO-04|Traffic between services, and between services and data stores or brokers, is encrypted in transit.⟧ |
| NFR-5 | Algorithms | ⟦S:CRYPTO-05|Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.⟧ |
| NFR-6 | Keys | ⟦S:CRYPTO-06|KMS holds the keys, the data stores only keep ciphertext, and key rotation happens at least yearly.⟧ |
| NFR-7 | Certificates | ⟦S:CRYPTO-07|TLS certificate verification is enabled in all clients, with no option to disable it.⟧ |
| NFR-8 | Secrets in artifacts | ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ |
| NFR-9 | Secrets at runtime | ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧ |
| NFR-11 | Network | ⟦S:NET-01|Databases and message brokers sit in private subnets and are not publicly reachable.⟧ |
| NFR-12 | Egress | ⟦F2|The sender follows redirects and calls any host, and there is no allow-list.⟧ |
| NFR-13 | Security logging | ⟦S:LOG-01|We log failed logins, changes of privileges and reads of sensitive data.⟧ |
| NFR-17 | Third parties | ⟦S:DATA-03|No personal data leaves for a third party without an approved DPA, and the payload is limited to the required fields.⟧ |
| NFR-18 | Test data | ⟦S:DATA-04|Test and staging environments use synthetic data, never real personal data or card data.⟧ |
| NFR-19 | Callbacks | ⟦S:API-03|Inbound and outbound webhooks include an HMAC signature and a timestamp; verification of both is mandatory on the receiving side.⟧ |
| NFR-20 | Queries | ⟦S:API-05|Database queries are parameterized, and user input is never concatenated into SQL.⟧ |
| NFR-21 | Pipeline | ⟦S:OPS-01|CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧ |
| NFR-22 | Containers | ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧ |

⟦S:AUTHZ-01|Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.⟧
⟦S:DATA-05|Reports and exports with personal data are available only to authorized users, stored encrypted, and deleted after 7 days.⟧
⟦S:API-01|Requests from outside are checked against the schema and rejected if they do not conform.⟧
⟦S:AUTHZ-04|Admin and debug endpoints are reachable only from the internal network, not from the public internet.⟧
⟦S:API-04|Internal details such as stack traces, SQL and hostnames never appear in an error response.⟧
⟦S:LOG-04|Reading centralized logs requires authorization, and only approved staff have it.⟧

## Design notes

Each notification has an id, a channel, a status (queued, sent, delivered, failed) and a reference to the recipient. Contact details are looked up at send time and are not copied into the notification. De-duplication uses the notification id so that a replayed event does not produce a second message. The consumer group is committed after the provider accepts the message, which gives at-least-once behavior with de-duplication on top.

## Definition of done

- All acceptance criteria demonstrated in staging.
- OpenAPI file updated.
- Dashboard for delivery rate and provider latency (owner TBD).

# Reference material for notifications

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
