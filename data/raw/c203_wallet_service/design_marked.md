# Wallet Service Design

## 1. Purpose

The Wallet Service keeps the balance of each customer wallet and executes top-ups, transfers between wallets and changes to the profile of the wallet owner. It is the backend of the Meridian Pay mobile app. This document describes the service behind the Mobile API Gateway, the data it keeps and the controls that protect it.

## 2. Architecture

The Mobile app calls the Mobile API Gateway. ⟦F2|The Mobile API Gateway is the only entrance for mobile traffic and forwards the requests of the app to wallet-core after it has checked the token of the customer with Keycloak.⟧ wallet-core holds the logic for balances and transfers and reads and writes wallet-db (PostgreSQL), where balances and transactions are stored.

## 3. Endpoints

- **GET /v1/wallets/{walletId}** returns the wallet with the fields id, owner_name, balance and currency.
- **POST /v1/wallets/{walletId}/topups** adds money from a funding source. The request carries amount and funding_source_id; the response returns id, type, amount and created_at.
- **POST /v1/transfers** moves money between two wallets. The request carries from_wallet_id, to_wallet_id, amount and note; the response returns id, type, amount and created_at.
- **GET /v1/wallets/{walletId}/transactions** lists the transactions of a wallet in pages, with the fields id, type, amount and created_at.
- **PATCH /v1/wallets/{walletId}/profile** changes owner_name, phone_number or address and returns the wallet.

A transfer between two wallets in the same currency is booked in one database transaction, so both balances change together or not at all. A wallet balance can never become negative; a transfer that would do that is rejected with the code `insufficient_funds`.

## 4. The mobile app

The mobile app for iOS and Android talks to the gateway over HTTPS. ⟦F1|The pin is the certificate of a single server of the gateway, and the app stops working when that certificate is renewed, so for those cases the support team tells users to turn pinning off in the developer menu until the next app release.⟧ The app shows the balance, the transaction list and the profile, and starts transfers with a confirmation by the customer.

⟦F3|After login, the app keeps the refresh token in the shared preferences of the app, so the customer does not have to sign in again when the app is restarted.⟧ The access token is requested again from Keycloak when it has expired.

## 5. Security controls

The team follows the Meridian Pay secure development guidelines for the wallet. Customers sign in with a password and a one-time code. ⟦S:IR-01|Alerts about repeated failed logins, privilege changes and access to card data reach the on-call engineer within 15 minutes.⟧ Every deployment is reviewed by a second engineer before it goes to production.

## 6. Data and recovery

wallet-db holds the wallets, the transactions and the profile data of the owners. ⟦S:DR-01|wallet-db has point-in-time recovery enabled, with seven days of retention.⟧ Balances are rebuilt from the transactions when the team runs the reconciliation job, which compares the sum of the transactions with the stored balance for every wallet once a night.

## 7. Failure modes

When wallet-db does not answer within two seconds, the gateway returns `service_unavailable` and the app shows a message that asks the customer to try again later. Top-ups are executed by the payment gateway of the funding source; when the answer is late, the top-up stays in the status `pending` and a job asks for the result every minute for ten minutes.

A transfer that has been booked cannot be undone through the wallet API. Mistaken transfers are corrected by the operations team through a reversing entry.

## 8. Rollout

The service replaces the wallet module of the monolith. The mobile app release 4.2 switches the app to the new endpoints. The release goes to ten percent of customers first, then to everyone after one week without a rise in failed transfers.

## 9. Open points

- The note field of a transfer is limited to 140 characters; the product team still has to decide whether emoji are allowed.
- The nightly reconciliation job runs at 02:00 UTC; the finance team asked for a second run at noon.
