# WAL-510: Wallet Service release 2

**Type:** Epic  **Priority:** High  **Component:** wallet  **Reporter:** Product & Platform

## Description

Second release of the Wallet Service. It keeps balances, executes top-ups and transfers and updates the profile of the wallet owner. The mobile app is the only client. Requirements of WAL-388 stay valid.

## User stories

**WAL-511** As a customer, I want to see my balance and currency.
Acceptance criteria:
1. GET /v1/wallets/{walletId} returns id, owner_name, balance and currency.
2. The balance equals the sum of the booked transactions.

**WAL-512** As a customer, I want to top up my wallet from a funding source.
Acceptance criteria:
1. POST /v1/wallets/{walletId}/topups accepts amount and funding_source_id.
2. The response returns id, type, amount and created_at.
3. A top-up that is not confirmed stays `pending` and is checked every minute for ten minutes.

**WAL-513** As a customer, I want to send money to another wallet.
Acceptance criteria:
1. POST /v1/transfers accepts from_wallet_id, to_wallet_id, amount and note.
2. Both balances change in one database transaction.
3. A transfer that would make the balance negative is rejected with `insufficient_funds`.

**WAL-514** As a customer, I want to read my transactions.
Acceptance criteria:
1. GET /v1/wallets/{walletId}/transactions returns id, type, amount and created_at in pages, newest first.

**WAL-515** As a customer, I want to change my name, phone number and address.
Acceptance criteria:
1. PATCH /v1/wallets/{walletId}/profile accepts owner_name, phone_number and address and returns the wallet.

## Non-functional requirements

**WAL-520** Customer rights.
Acceptance criteria:
1. Requests of customers to see or delete their personal data are answered within 30 days and recorded in the request register.

**WAL-521** Data location.
Acceptance criteria:
1. Backups and replicas of the personal data of customers in the EU stay in regions of the EU as well.

**WAL-522** Delivery.
Acceptance criteria:
1. Credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour.
2. Build artifacts are signed, and the signature is verified before deployment.
3. Database migrations of the release cannot be rolled back, and no other recovery is planned for them.

**WAL-523** Observability.
Acceptance criteria:
1. Error traces include the full request that failed, including the card number that did not pass the validation.

**WAL-524** Behaviour under load.
Acceptance criteria:
1. When the capacity of a public endpoint is exhausted, the endpoint answers HTTP 503 and does not queue the requests.
2. Every feature that moves money has a kill switch, and the kill switch is tested every quarter.

## Rollout

WAL-530: the release goes with the mobile app 4.3, to ten percent of the customers first and to everyone after one week without a rise in failed transfers (see WAL-399).
