# Payment Gateway: Design Specification

## 1. Purpose and scope

This document specifies the Payment Gateway of Meridian Pay in accordance with company policy and the applicable regulatory framework. The service accepts card payments from merchants, routes them to the acquiring banks and publishes the status of every payment. It replaces the payment module of the monolith.

## 2. Architecture

The Payments Edge Gateway receives the requests of the merchant backends and passes them to payments-core. payments-core holds the lifecycle of a payment, stores the payment records in payments-db (PostgreSQL), calls the acquirers through the Acquirer connector and publishes the status events to payment-events (Kafka).

## 3. Interfaces

**POST /v1/payments** creates a payment. It takes amount, currency, card_token, merchant_id and reference and returns id, status, amount, currency, last4 and merchant_id.

**GET /v1/payments/{paymentId}** returns one payment with the same fields. **GET /v1/payments** lists the payments of a merchant in pages.

**POST /v1/payments/{paymentId}/capture** captures an authorized payment with an amount, which may be lower than the authorized one.

**POST /v1/payments/{paymentId}/refunds** refunds a captured payment; it takes amount and reason and returns id, status and amount.

## 4. Capacity and delivery

Load shedding exists for the create-payment endpoint, which is the busiest one; the other endpoints rely on the capacity of the gateway and queue requests when it is exceeded. In accordance with company policy the service is delivered through the pipeline of the platform team.

The credentials of the pipeline are stored as variables of the pipeline project, and all developers of the platform team can read them. Build artifacts are signed, and the signature is verified before deployment.

## 5. Change and data location

Every change to production has a rollback plan that has been tested in a pre-production environment. Backups and replicas of the personal data of customers in the EU stay in regions of the EU as well.

## 6. Failure handling

When the acquirer does not answer in three seconds, the payment stays `pending`, and payments-core asks for the result up to five times. After the fifth attempt the payment is declined with the reason `acquirer_timeout`. Events are written to an outbox table when Kafka is not reachable.

## 7. Rollout

The service is introduced in three steps: new merchants, existing merchants in groups of fifty, and the switch-off of the old module one month after the last group.

## 8. Open questions

- Whether the list endpoint filters by status in the first release.
- Whether partial captures publish their own event.
