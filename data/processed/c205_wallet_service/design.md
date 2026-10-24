# WAL-410: Wallet Service on the new platform

**Type:** Epic  **Priority:** High  **Component:** wallet  **Reporter:** Product & Platform

## Description

Move the wallet functions from the monolith to the Wallet Service. The service keeps balances, executes top-ups and transfers and updates the profile of the wallet owner. The mobile app is the only client. The requirements of the related ticket WAL-388 stay valid.

## User stories

**WAL-411** As a customer, I want to see the balance and the currency of my wallet so that I know what I can spend.
Acceptance criteria:
1. GET /v1/wallets/{walletId} returns id, owner_name, balance and currency.
2. The balance equals the sum of the booked transactions.

**WAL-412** As a customer, I want to top up my wallet from a funding source so that I can pay and send money.
Acceptance criteria:
1. POST /v1/wallets/{walletId}/topups accepts amount and funding_source_id.
2. The response contains id, type, amount and created_at.
3. A top-up that is not confirmed by the funding source stays `pending` and is checked every minute for ten minutes.

**WAL-413** As a customer, I want to send money to another wallet so that I can pay a friend.
Acceptance criteria:
1. POST /v1/transfers accepts from_wallet_id, to_wallet_id, amount and note.
2. Both balances change in one database transaction.
3. A transfer that would make the balance negative is rejected with `insufficient_funds`.
4. Every payment operation request carries an idempotency key, and a repeated key returns the original result without repeating the operation.

**WAL-414** As a customer, I want to read my transactions so that I can check my spending.
Acceptance criteria:
1. GET /v1/wallets/{walletId}/transactions returns id, type, amount and created_at in pages, newest first.

**WAL-415** As a customer, I want to change my name, phone number and address so that the wallet stays up to date.
Acceptance criteria:
1. PATCH /v1/wallets/{walletId}/profile accepts owner_name, phone_number and address.
2. The response returns id, owner_name, balance and currency.

## Architecture

The Mobile app calls the Mobile API Gateway. The Mobile API Gateway validates the token of the customer with Keycloak and forwards the request to wallet-core, which keeps the state in wallet-db (PostgreSQL), and the app keeps the session of the customer between the starts of the application.

## Non-functional requirements

**WAL-420** Mobile app connections.
Acceptance criteria:
1. The mobile app pins the public key of the Meridian Pay API and refuses every connection that fails the pinning check.

**WAL-421** Alerting.
Acceptance criteria:
1. Alerts about repeated failed logins, privilege changes and access to card data reach the on-call engineer within 15 minutes.

**WAL-422** Third-party components.
Acceptance criteria:
1. The list of approved third-party components exists, and it was last reviewed two years ago, when the wallet was still part of the monolith.
2. The list is kept in the wiki of the platform team.

## Rollout

WAL-430: the service goes live with the mobile app release 4.2. The release reaches ten percent of customers first, and everyone after one week without an increase in failed transfers. The old module stays available for one more month (see WAL-399 for the switch-off checklist).

## Out of scope

Card top-ups from the app, scheduled transfers and multi-currency wallets are covered by separate epics.
