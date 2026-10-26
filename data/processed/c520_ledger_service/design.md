# Ledger Service - Business and Technical Overview

## 1. Why a new ledger

Meridian Pay grows fast, and the wallet and the payment services each keep their own balances. The Ledger Service gives the whole platform one enterprise-grade source of truth for money: every movement is a balanced journal entry, and every balance is the sum of entries. The service is secure by design, scalable and ready for the next ten years of growth. It is used by internal services only.

## 2. Capabilities

- Post a balanced journal entry with a debit account, a credit account, an amount, a currency and a reference.
- Read an entry, read the balance of an account, list entries and reverse an entry with a reason.
- Publish every posted entry as an event for reporting and reconciliation.

## 3. Components

ledger-core is the service that validates and posts entries. ledger-db (PostgreSQL) stores entries and balances. ledger-events (Kafka) carries the posted-entry events. The wallet and payment services call ledger-core; nobody outside the platform does.

## 4. Interfaces

| Call | Purpose | Request | Response |
|---|---|---|---|
| POST /v1/entries | post an entry | debit_account, credit_account, amount, currency, reference | id, debit_account, credit_account, amount, posted_at |
| GET /v1/entries/{entryId} | read an entry | none | same fields |
| GET /v1/accounts/{accountId}/balance | read a balance | none | account_id, balance, currency |
| POST /v1/entries/{entryId}/reversal | reverse an entry | reason | same fields as an entry |
| GET /v1/entries | list entries | none | same fields as an entry |

## 5. Money features and their safety

The ledger is a world-class foundation for all money features of the company. The kill switch of the ledger is tested once a year, before the annual audit. A reversal never deletes the original entry, it posts a mirror entry.

## 6. Delivery

The business value of fast delivery is high, and the platform pipeline makes it safe. Credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour. ledger-core is released through the standard process of the platform, as with every other service of the company.

## 7. Observability

The dashboards show the number of posted entries per minute and the age of the oldest unpublished event. Traces and metrics do not contain personal data or card data.

Every service exposes a health endpoint that the shared dashboard polls every minute, and the error rate of each endpoint is shown on the dashboard.

Every change to production must be reviewed by a second engineer before it is deployed.

## 8. Failure handling

If ledger-events is not reachable, the posted entries wait in an outbox table and are published in order afterwards. If the same reference is posted twice, the second call returns the first entry.

## 9. Roadmap

The first release serves the wallet service. The payment service follows one quarter later, and the reconciliation reports are the third step.
