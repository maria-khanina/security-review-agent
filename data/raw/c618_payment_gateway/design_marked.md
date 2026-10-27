# Payment Gateway - Architecture and Operations

## 1. Purpose

The Payment Gateway accepts card payments from merchants, routes them to the acquirers and publishes payment events. It is the only entry point for merchant payments.

## 2. Architecture

The Payments Edge Gateway receives the requests from the merchants and forwards them to payments-core. The payments-core service holds the payment logic and stores payments in payments-db (PostgreSQL). It calls the Acquirer connector, a third party, for authorization and capture, and publishes events to payment-events (Kafka).

## 3. Interface

The interface consists of the following operations: creation of a payment, retrieval, capture, refund and listing of payments (POST /v1/payments, GET /v1/payments/{paymentId}, POST /v1/payments/{paymentId}/capture, POST /v1/payments/{paymentId}/refunds, GET /v1/payments).

## 4. Notifications to merchants

⟦F1|Callbacks to the merchants are plain HTTP requests, and the secret of the merchant is part of the URL.⟧

## 5. Operations

5.1 Alerts. Alerts about the gateway are routed to the on-call engineer. ⟦F2|The acknowledgement time is measured from the moment the engineer opens the ticket.⟧

5.2 Test environments. ⟦F3|Test accounts that were created in production are disabled after the test, but they are not deleted.⟧

5.3 ⟦S:VUL-02|Third-party components are not more than two major versions behind the latest release, and the service register shows the version of each.⟧

## 6. Obligations

6.1 ⟦S:ARC-01|Transaction records are retained for 7 years and deleted within 90 days after that period.⟧

6.2 ⟦S:NTF-01|Messages to customers do not contain card numbers, passwords or images of identity documents.⟧

6.3 ⟦S:INV-01|The service register names an owner and a deputy of the gateway.⟧ ⟦S:INV-02|It lists the personal data that the gateway processes and each third party that receives data, among them the acquirers.⟧

