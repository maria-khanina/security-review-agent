# Wallet Service: Design

Owner: Consumer Payments team
Status: approved for build

## 1. Purpose

The Wallet Service keeps the balance of each customer wallet and executes top-ups, transfers between wallets and changes to the profile of the wallet owner. It is the backend of the Meridian Pay mobile app. This document describes the service behind the Mobile API Gateway, the data it keeps and how it is operated.

## 2. Architecture

The mobile app calls the Mobile API Gateway, which checks the token of the customer with Keycloak and forwards the request to wallet-core. ⟦F3|wallet-core runs as three replicas and takes over the logic for balances and transfers, and it reads and writes wallet-db (PostgreSQL).⟧ wallet-db holds the balances and the transactions.

## 3. Endpoints

- **GET /v1/wallets/{walletId}** returns id, owner_name, balance and currency.
- **POST /v1/wallets/{walletId}/topups** adds money from a funding source. It takes amount and funding_source_id and returns id, type, amount and created_at.
- **POST /v1/transfers** moves money between two wallets. It takes from_wallet_id, to_wallet_id, amount and note and returns id, type, amount and created_at.
- **GET /v1/wallets/{walletId}/transactions** lists the transactions of a wallet in pages, with id, type, amount and created_at.
- **PATCH /v1/wallets/{walletId}/profile** changes owner_name, phone_number or address and returns the wallet.

A transfer between two wallets in the same currency is booked in one database transaction. A wallet balance never becomes negative.

## 3.1 Customers and their data

⟦F1|Requests of customers to delete their data go to the support mailbox and are handled when the team has time, which in practice can take several months.⟧ The profile of a wallet holds the name, the phone number and the address of the owner.

## 4. Data and its place

⟦S:RES-02|Backups and replicas of the personal data of customers in the EU stay in regions of the EU as well.⟧ Balances can be rebuilt from the transactions with a nightly job that compares the sum of the transactions with the stored balance of each wallet.

## 5. Delivery and operation

The service is built and deployed by the pipeline of the platform team. ⟦F2|The pipeline uses one set of credentials that is shared by the pipelines of the wallet team and the payments team, so that the two teams do not have to maintain separate ones.⟧ ⟦S:PIP-02|Build artifacts are signed, and the signature is verified before every deployment.⟧ ⟦S:CHG-02|Every change to production has a rollback plan that has been tested in a pre-production environment.⟧

⟦S:OBS-01|Traces and metrics contain neither personal data nor card data.⟧ The dashboards show the latency of each endpoint, the error rate and the number of transfers per minute.

## 6. Failure modes

When wallet-db does not answer within two seconds, the gateway returns `service_unavailable`. A top-up that the funding source has not confirmed stays `pending`, and a job asks for the result every minute for ten minutes. A booked transfer cannot be undone through the API; mistakes are corrected by the operations team through a reversing entry.

## 7. Rollout

The service replaces the wallet module of the monolith. The mobile app release 4.2 switches to the new endpoints, first for ten percent of the customers and then for everyone after a week without a rise in failed transfers.

## 8. Open points

- The note of a transfer is limited to 140 characters; whether emoji are allowed is open (TBD).
- The nightly job runs at 02:00 UTC; the finance team asked for a second run at noon (TBD).
