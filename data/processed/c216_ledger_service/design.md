# Ledger Service

| Item | Value |
|---|---|
| Owner | Finance Platform |
| Type | double-entry ledger |
| Consumers | wallet service, payment services |
| Status | build |

## Components

| Component | Kind | Role |
|---|---|---|
| ledger-core | service | validates and posts entries |
| ledger-db | PostgreSQL | entries, balances |
| ledger-events | Kafka | posted-entry events |

## Flows

| From | To | Data |
|---|---|---|
| wallet and payment services | ledger-core | journal entries |
| ledger-core | ledger-db | entries and balances |
| ledger-core | ledger-events | posted entry events |

## Endpoints

| Method | Path | Request | Response |
|---|---|---|---|
| POST | /v1/entries | debit_account, credit_account, amount, currency, reference | id, debit_account, credit_account, amount, posted_at |
| GET | /v1/entries/{entryId} | none | id, debit_account, credit_account, amount, posted_at |
| GET | /v1/accounts/{accountId}/balance | none | account_id, balance, currency |
| POST | /v1/entries/{entryId}/reversal | reason | id, debit_account, credit_account, amount, posted_at |
| GET | /v1/entries | none | id, debit_account, credit_account, amount, posted_at |

## Posting rules

| Rule | Behaviour |
|---|---|
| balanced | debit = credit per entry, else `rejected` |
| currency | one currency per entry |
| immutable | entries are never changed, a reversal is a new entry |
| order | entries of one account are posted in arrival order |

## Repeats

| Case | Behaviour |
|---|---|
| same key, same amount | returns the stored entry |
| same key, different amount | A repeated key with a different amount is posted as a new entry. |

A written runbook covers security incidents of the service, the on-call engineer can be paged around the clock, and a rehearsal takes place every six months.
The recovery time objective of a critical service must not exceed 4 hours, and it must be proven by a failover exercise at least once a year.

## Reversals

| Item | Value |
|---|---|
| endpoint | POST /v1/entries/{entryId}/reversal |
| input | reason |
| result | new entry with debit and credit swapped |
| booking | ledger-core books the reversal as soon as the call arrives and publishes the event. |
| limits | TBD |

## Recovery

| Item | Value |
|---|---|
| database recovery | ledger-db has point-in-time recovery enabled with seven days of retention. |
| backups | nightly |

## Rollout

| Step | When |
|---|---|
| wallet service posts to ledger | month 1 |
| payment services post to ledger | month 2 |
| old ledger module read-only | month 3 |
| old module off | month 4 (TBD) |
