# Ledger Service: changes compared with the ledger module of the monolith

This document describes only what changes. Everything that is not mentioned here (account structure, posting rules, rounding, the meaning of the references) stays as in the old ledger module.

## What changes

**Where the ledger runs.** The ledger moves out of the monolith into its own service, ledger-core. The wallet and payment services call ledger-core over HTTP instead of calling the module in the same process. ledger-core writes the entries and balances to ledger-db (PostgreSQL), which is a new database; the old tables stay in the monolith until the migration is finished.

**How entries are posted.** Before, callers wrote a row to the ledger table inside their own transaction. Now they call `POST /v1/entries` with debit_account, credit_account, amount, currency and reference, and get id, debit_account, credit_account, amount and posted_at back. The check that debit equals credit moves from the database trigger into ledger-core.

**How entries are read.** `GET /v1/entries/{entryId}` and `GET /v1/entries` return the same fields as the post call. `GET /v1/accounts/{accountId}/balance` returns account_id, balance and currency, and replaces the balance view of the old module.

**How mistakes are corrected.** `POST /v1/entries/{entryId}/reversal` takes a reason and creates a new entry with debit and credit swapped. In the old module the same was done by hand with a script.

**Events.** Before, consumers polled the ledger table. Now ledger-core publishes every posted entry to ledger-events (Kafka), and the consumers subscribe.

## What does not change

- The account numbers and the structure of the chart of accounts.
- Entries are never edited or deleted.
- The nightly check that the sum of all entries equals the sum of all balances still runs at 01:00 UTC; it now reads ledger-db.

## Operation

Security-relevant events of ledger-core are collected on the operations dashboard, as for the old module, and nobody is paged from it. ledger-db has point-in-time recovery enabled, with seven days of retention. The recovery plan assumes a restore of ledger-db from the nightly backup, which takes about a day.

A written runbook covers security incidents of the service, the on-call engineer can be paged around the clock, and a rehearsal takes place every six months.

## Migration steps

1. Month 1: the wallet service posts to ledger-core and to the old module in parallel; a daily comparison shows the differences.
2. Month 2: the payment services follow.
3. Month 3: the old ledger module becomes read-only.
4. Month 4: the old tables are archived and removed (see the cleanup list of the monolith, which is not up to date).

## Open points

The old module allowed entries in a currency that differs from the one of the account. The new service rejects them; the finance team still has to confirm that no process depends on the old behavior.
