# Payment Gateway: Design and Operating Concept

## 1. Purpose and scope

The Payment Gateway accepts card payments from merchants, routes them to the acquirers and publishes the status of every payment as an event. This document describes the service, its data, its delivery and its operation. The design follows the Meridian Pay secure development guidelines and the lessons of the pilot.

## 2. Architecture

A merchant backend calls the Payments Edge Gateway with a payment request that carries a card token. The gateway passes validated requests to payments-core. payments-core holds the lifecycle of a payment, talks to the Acquirer connector and writes the payment records to payments-db (PostgreSQL). Status events go to the payment-events topic (Kafka).

## 3. Endpoints

- **POST /v1/payments** creates a payment from amount, currency, card_token, merchant_id and reference, and returns id, status, amount, currency, last4 and merchant_id.
- **GET /v1/payments/{paymentId}** returns one payment with the same fields.
- **POST /v1/payments/{paymentId}/capture** captures an authorized payment; the request carries the amount.
- **POST /v1/payments/{paymentId}/refunds** refunds a captured payment; it takes amount and reason and returns id, status and amount.
- **GET /v1/payments** lists the payments of a merchant in pages.

## 4. Data and its place

payments-db holds the payment records with the last four digits of the card and the merchant id. The region of payments-db was never chosen explicitly and follows the default of the cloud account, which is the region where the account was opened. Backups and replicas of the personal data of customers in the EU stay in regions of the EU as well.

## 5. Security controls

Merchants authenticate with signed requests, and tokens replace card numbers everywhere outside the vault. The following controls apply to the service.

- Traces and metrics do not contain personal data or card data.
- The purposes of personal data are listed in the privacy notice that customers accept at sign-up, and the data is not used for any purpose outside that list.
- Every change to production is reviewed by a second engineer before deployment.
- When the capacity of a public endpoint is exhausted, the endpoint answers HTTP 503 and does not queue the requests.
- Credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour.
- Health check results and error rates are published to the shared dashboard every minute, and an alert fires when the error rate stays above 2% for five minutes.
- Every change to production has a rollback plan that has been tested in a pre-production environment.
- Build artifacts are signed by the pipeline, and the signature is checked in the test environment but not in production, where the deployment tool does not support the check yet.

The team is working on a hardware-backed signing key, which is planned for the next year.

## 6. Failure handling

When the acquirer does not answer within three seconds, payments-core keeps the payment `pending` and asks for the result up to five times with growing pauses; after that the payment is declined with the reason `acquirer_timeout`. When Kafka is not reachable, events are written to an outbox table and published later in order.

## 7. Rollout

The rollout has three waves: new merchants, existing merchants in groups of about fifty, and the switch-off of the old endpoints a month after the last group.
