# data warehouse sync - design meeting (notes)

Attendees: Petra, Jonas, Amir, Lena (joined late)
Notes: Amir
Old doc: "analytics-feed" page on the previous wiki (link dead)

## context

Goal: copy the tables the analytics vendor needs from the production replica into a staging bucket every night, so the vendor can load them into their warehouse. Replaces the old CSV mails that Jonas sent by hand. The thing that does the copy is the sync-job (a.k.a. "the feeder" in the old doc). It reads from the analytics read replica (PostgreSQL), writes extract files to the staging bucket (S3), the vendor picks up the files from there. Terraform names: warehouse_key, staging_bucket, analytics_replica, analytics_sg, sync_audit, sync_job_policy.

## discussion

**What goes into the extracts.** The sync-job copies the selected tables from the analytics read replica into one extract file per table. Which columns exactly - Petra says the vendor "will tell us what they need", Jonas thinks we start with everything and trim later (TBD, nobody decided).

**Vendor.** The extract files are sent to the analytics vendor under a verbal agreement, and the written contract will follow once the pilot is over. Lena (late) asked if legal knows, nobody could say (TBD, Amir to ask legal).

**Download.** Vendor needs to pull the files without us creating links every night. The reports are served from a publicly readable bucket, so that nobody has to generate download links. Petra not happy, Jonas says it is only for the pilot (TBD).

**Access and platform.** Short list from the platform checklist, nobody objected:
- Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.
- Internal users are given the minimum set of roles for their job, and roles are defined service by service.
- Access lists are reviewed only before an external audit.
- The databases and object stores that hold PII use AES-256 encryption at rest.
- Log access is granted to whole teams and is never removed.
- Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.
- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- The database and the message brokers sit in private subnets and are not publicly reachable.
- Admin and debug endpoints are reachable only from the internal network, not from the public internet.
- On boot, the service pulls its credentials from the approved secret store.
- Authentication failures, privilege changes and access to sensitive data are written to the logs.
- All queries use bound parameters instead of string concatenation.

**Schedule.** Run at 03:00, takes about 20 min for the current table set. If a run fails nothing is overwritten and the vendor keeps yesterday's files. Alert goes to #data-eng (weekend routing TBD).

## action items

- Amir: ask legal about the vendor contract (TBD)
- Jonas: list of columns with Petra (TBD)
- Petra: decide with Jonas if the bucket stays as it is after the pilot (TBD)
- Lena: nothing, was late

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

# Appendix 1: related system, Wallet Service; reference material for the wallet

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
