# Ledger Service - Design Document

Author: Andrei V., Finance Platform team
Status: Ready for review

## 1. Introduction

Ledger Service keep the record of all the money movements of Meridian Pay. Every top-up, payment and refund is written like a journal entry with the debit side and the credit side. Before this the ledger was a module inside the monolith. Now it is a separate service with own database and own event stream. This document describe the design and the security controls.

## 2. Components

- **ledger-core** - the service. It accept the entries, check that they balance, write them and answer about balances.
- **ledger-db (PostgreSQL)** - the database with entries and balances.
- **ledger-events (Kafka)** - the stream where one event is published for each posted entry.

The wallet and payment services send the entries to ledger-core. Ledger-core write them in ledger-db and publish the event on ledger-events.

## 3. API

- POST /v1/entries - post an entry. The caller send debit_account, credit_account, amount, currency and reference. The reply contain id, both accounts, the amount and posted_at.
- GET /v1/entries/{entryId} - give one entry.
- GET /v1/accounts/{accountId}/balance - give the balance and the currency of the account.
- POST /v1/entries/{entryId}/reversal - reverse the entry, with a reason.
- GET /v1/entries - list of the entries.

Card numbers are never returned by the API. All state-changing operations require an authenticated caller.

## 4. Rules of the ledger

There are four rules. First, double entry: the debit and the credit of every entry must be equal. Second, nothing is changed: an entry is never edited and never deleted, a mistake is corrected with a reversal. Third, the balance is calculated from the entries, nobody edit it directly. Fourth, the same reference posted two times return the first entry, so a retry is safe. If the two sides of the entry have different currency, the entry is rejected, because the conversion is the job of the caller.

## 5. Access and secrets

⟦S:AUTH-02|The calls from the internal services to ledger-core are authenticated with mutual TLS or signed workload identity tokens.⟧ ⟦S:AUTHZ-02|Internal users receive only the roles which are required for their job, and the roles are defined per service.⟧ ⟦S:AUTHZ-05|Access to production is recertified at least once per quarter.⟧

⟦S:SECRET-01|Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.⟧

## 6. Cryptography and network

⟦S:CRYPTO-05|We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.⟧ ⟦S:NET-01|The database and the message brokers are in the private subnets and are not publicly reachable.⟧

⟦S:SECRET-02|Runtime secrets must be fetched from the approved secret store at startup.⟧

⟦S:API-01|Schema validation runs on every external input, and invalid data never reaches the business logic.⟧

⟦S:AUTHZ-04|Debug and administrative routes are not exposed to the internet.⟧

## 7. Logging, queries and operations

⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are written to the logs.⟧ ⟦S:API-05|User input reaches the database only as query parameters, never as part of the query text.⟧

⟦S:LOG-04|Access to centralized logs must be limited to authorized staff.⟧

## 8. How posting works

The posting is one database transaction. The entry and a row of the outbox are written together, and a relay publish the event after it, so an event is never published for an entry which was not saved. The balance is not stored in a field, it is calculated from the entries with a query on the account index. If the read load grow, a materialized view is the plan (TBD).

A reversal is a normal entry with the debit and the credit exchanged and a link to the original entry. One entry can be reversed one time. The original stay as it was, so the history is complete: the mistake, the reversal and the correct entry.

## 9. Reconciliation

Every night a job compare the sum of all entries with the sum of all balances and send an alert if they are not equal. The finance engineer on call investigate the difference and correct it with a reversal, never with a deletion.

## 10. Open points

- Size of the page of the list (TBD).
- Does the balance call need a cache of one second? Finance say no.
