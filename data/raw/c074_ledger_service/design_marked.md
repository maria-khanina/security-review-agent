# Ledger Service - Design Document

Author: Dmitri K., Finance Platform team
Status: Draft, please read and comment

## 1. Introduction

Ledger Service is the service who keep the financial truth of Meridian Pay. Every movement of money, from the wallet or from the payments, is write here like a journal entry with the debit side and the credit side. The service is new, before this the ledger was a module inside the big monolith what everybody afraid to touch. The goal of this document is to explain the design and the behaviour for the people from wallet, payments and finance teams.

## 2. The components

There are three parts.

- **ledger-core** is the service itself. It accept the entries, check them, write them and answer the questions about balances.
- **ledger-db (PostgreSQL)** is the database with entries and balances.
- **ledger-events (Kafka)** is the stream where we publish one event for each posted entry, so the other teams can react without ask us.

The wallet and payment services send the entries to ledger-core. Ledger-core write the entries and the balances to ledger-db and publish the events to ledger-events.

⟦F1|ledger-db (PostgreSQL) is the system of record for all the entries and the balances, and it run as a primary with one standby.⟧

## 3. The API

The API have five calls.

- POST /v1/entries post an entry. The caller send debit_account, credit_account, amount, currency and reference. The answer contain the id, both accounts, the amount and the time of posting.
- GET /v1/entries/{entryId} return one entry in the same shape.
- GET /v1/accounts/{accountId}/balance return the account, the balance and the currency.
- POST /v1/entries/{entryId}/reversal reverse an entry. The only field is the reason.
- GET /v1/entries return the list of entries, the newest first.

The API enforces per-client rate limits. The limits are different for the wallet, the payments and the reporting clients.

## 4. Rules of the ledger

We have four rules and everybody must respect them. First, double entry: every entry have the debit and the credit and they must be equal. Second, nothing is changed: an entry is never edited or deleted, if there is a mistake we post a reversal. Third, the balance is calculated from the entries and nobody can edit the balance directly. Fourth, the same reference posted two times give the first entry back, so a retry is safe.

If the two sides of an entry have different currencies the entry is rejected. The conversion of currency is the job of the caller, not of the ledger.

## 5. How ledger-core works

⟦F2|ledger-core accept the entries, check that they balance, and keep them safe, so the other services can trust the numbers.⟧ The posting is one database transaction. The entry and a row for the outbox are written together, and a relay publish the event after it. In this way an event is never published for an entry that was not saved.

⟦F3|ledger-core write the records about its work, and the operations team can read them when they need to understand a problem.⟧

## 6. Security controls

The controls which are important for this service are listed here.

- ⟦S:SECRET-01|Source, config, specs and infrastructure definitions contain no secrets.⟧
- ⟦S:AUTHZ-01|The service compares the authenticated caller with the owner of the requested resource and rejects the request if they do not match and no entitlement exists.⟧
- ⟦S:SECRET-02|The runtime secrets are fetched from the approved secret store when the service start.⟧
- ⟦S:API-05|All queries use bound parameters instead of string concatenation.⟧
- ⟦S:OPS-01|Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less.⟧
- ⟦S:LOG-03|The audit trail is tamper-evident, and we keep it for no less than twelve months.⟧
- ⟦S:AUTH-03|Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.⟧
- ⟦S:AUTH-02|We do not trust the internal network by itself: every internal call is authenticated with mTLS or workload identity tokens.⟧
- ⟦S:AUTHZ-03|A separate account is created for this service with grants limited to the tables it uses and to the operations it needs, and shared administrative credentials are not used by the application.⟧
- ⟦S:AUTHZ-04|Debug and administrative routes are not exposed to the internet.⟧

## 7. Balance and reconciliation

The balance of an account is the sum of all its entries. It is not saved in a field that somebody can edit. Every night a job compare the sum of all the entries with the sum of all the balances and send an alert if the numbers are not the same. Finance read the result of this job in the morning. If the job find a difference, the finance engineer on call start the investigation and the reversal is used to correct the mistake, never the deletion.

## 8. Reversal

A reversal is a normal entry with the debit and the credit exchanged, and a link to the original entry. One entry can be reversed one time. The original entry stay as it was, so the history is complete: first the mistake, then the reversal, then the correct entry.

## 9. Rollout

The rollout is in three waves. In the first wave the entries from the old wallet tables are copied to the ledger in shadow mode, and finance compare the numbers. In the second wave the ledger become the authority for the wallet balances. In the third wave the payments move. After each wave finance sign off one full day of reconciliation. Any wave can fall back to the old tables during the shadow and the authority phases.

## 10. Open points

- Maximal size of the page of the list.
- Should the balance call have a cache of one second? Finance say no.
- TBD: name of the new Kafka topic (see the old proposal, the link is dead).
