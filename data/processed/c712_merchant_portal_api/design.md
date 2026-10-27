# Merchant Portal API - Design

## Overview

The portal is the back office for merchants: settlements, users, reports. Portal Gateway in front, portal-backend behind, portal-db (PostgreSQL) for data, Keycloak for login, and the Merchant web app as client. The portal-backend reads the settlements from portal-db and builds the reports on request.

## Endpoints

- GET /v1/settlements
- GET /v1/settlements/{settlementId}
- POST /v1/users
- PATCH /v1/users/{userId}/role
- POST /v1/reports
- GET /v1/reports/{reportId}

## Quality commitments

1. Money. Every operation that moves money takes an idempotency key, and a repeated request with the same key does not move the money again.
2. Reconciliation. Balances are compared with the ledger once a month, when finance closes the books.
3. API versions. Old API versions are retired without a date, and customers find out when their calls fail.
4. Sandbox. The merchant sandbox contains only generated data and runs separately from production.
5. Messaging and jobs. Messages that cannot be processed go to a dead-letter queue, which is examined within one working day. Messages are deleted from the queue after they are processed. Every scheduled job runs with its own service account, which cannot log in interactively.
