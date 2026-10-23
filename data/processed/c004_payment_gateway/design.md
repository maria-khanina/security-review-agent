# Payment Gateway Service - Design Document

Author: Dmitri K., Payments Platform team
Status: Draft for review

## 1. Overview

Payment Gateway is the service who accepts card payments from our merchants, routes them to the acquiring banks and publish the status events for other teams. Merchants never send us the card number: their backend send us a card token and we work only with this token. The goal for this quarter is to move the old monolith endpoints to this new service without changing the contract for merchants.

Public API (OpenAPI spec is in the repository):

- POST /v1/payments - create a payment
- GET /v1/payments/{paymentId} - get the payment
- POST /v1/payments/{paymentId}/capture - capture an authorized payment
- POST /v1/payments/{paymentId}/refunds - refund a payment
- GET /v1/payments - list and search the payments of a merchant

## 2. Architecture

The request come from the merchant backend to Payments Edge Gateway. The gateway do the first checks and forward the validated request to payments-core. The payments-core is the main service with the business logic. It write the payment records to payments-db (PostgreSQL), it send the authorization request to the acquirer through Acquirer connector, and after every status change it publish an event to payment-events (Kafka) which is consumed by ledger and notification teams.

There are five components: Payments Edge Gateway, payments-core, payments-db, Acquirer connector and payment-events. Onboarding of new acquirers is described on the Confluence page "Acquirer onboarding" (link will be added).

## 3. Authentication and authorization

Every call to the public API is authenticated at Payments Edge Gateway with OAuth2 bearer tokens issued by our identity provider. A request without valid token is rejected with 401 before it reach payments-core.

On every request for a payment, payments-core check that the calling merchant is the owner of this payment. This check is not skipped for GET and list calls.

Administrative and debug endpoints are not published on the public gateway and cannot be reached from internet. Operators use the internal network only.

## 4. Data protection

The service handle card data and personal data of the payer. We have rules for both.

Primary account numbers are never stored in clear text, the card token vault is the only place that know them and we keep only tokens and last four digits.

Personal data in payments-db is encrypted at rest with AES-256.

 Plain HTTP is closed on the gateway.

We use only approved cryptographic algorithms; MD5, SHA-1, DES, 3DES and ECB mode are forbidden.

Credentials are never committed to code, configuration, specifications or infrastructure-as-code files. The runtime secrets are fetched from the approved secret store when service start.

Payment records have a retention period of seven years after the transaction, then a scheduled job delete them; a verified request from the data subject is also honored when no legal hold exists.

Payer data is sent to the acquirer only under the approved data processing agreement, and we send only the fields the acquirer need for authorization.

## 5. API behaviour

All input of the public API is validated against the OpenAPI schema and invalid requests are rejected with 400. Browser calls are accepted only from the approved origins in CORS list.

For the search endpoint GET /v1/payments the merchant can filter by merchant_id and status. For this search we build the WHERE part of the SQL query by concatenating the filter values in the query string, because it is more simple and faster than prepared statements for the dynamic filters.

## 6. Logging and operations

Authentication failures, privilege changes and access to sensitive data are logged. Logs carry opaque identifiers only and never include secrets, card numbers or personal data.

About the build: the dependencies are pinned on the versions what we validated in 2022 and we do not run any automatic vulnerability scanner in the pipeline, because we want stable builds and no surprise upgrades. Updates are made by hand when somebody has time. TBD: who is owner of this.

## 7. Open points

- TBD: final decision about retry policy to acquirer connector when timeout
- Idempotency key for POST /v1/payments is discussed with the merchant team
