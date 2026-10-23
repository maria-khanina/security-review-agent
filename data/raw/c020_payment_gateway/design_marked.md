# Payment Gateway: Design Document (written as a learning exercise)

Author: Marcus, junior engineer, Payments team
Mentor: Dana (please review)

## 1. Why do we need a payment gateway?

When a customer pays a merchant with a card, a lot of things have to happen: the merchant has to ask the card network if the money is available, the money has to be reserved, later it has to be moved, and sometimes it has to be given back. A payment gateway hides this complexity behind a simple API. The merchant backend sends one request and gets back one answer, and our gateway talks to the acquiring bank for them.

## 2. The parts

- **Payments Edge Gateway** is the public entrance. All merchant traffic comes through it.
- **payments-core** is the service with the payment rules and states.
- **payments-db (PostgreSQL)** stores payments.
- **Acquirer connector** is the adapter that talks to the acquiring bank.
- **payment-events (Kafka)** is a stream where we publish an event each time a payment changes status, so other teams can react.

The merchant backend sends a payment request with a card token (not the card number). The edge gateway checks it and forwards the validated request to payments-core. payments-core saves it in payments-db, calls the acquirer through the connector, and publishes an event.

## 3. The API

- POST /v1/payments creates a payment. Fields: amount, currency, card_token, merchant_id and reference. The reply has id, status, amount, currency, last4 and merchant_id.
- GET /v1/payments/{paymentId} returns a payment.
- POST /v1/payments/{paymentId}/capture captures an authorized payment; the only field is amount.
- POST /v1/payments/{paymentId}/refunds refunds a payment with amount and reason, and returns id, status and amount.
- GET /v1/payments lists payments.

The difference between authorize and capture confused me at first. Authorize means "reserve the money", capture means "take the reserved money". A refund gives money back after capture.

## 4. Authentication

In a gateway, authentication answers "who is calling?". ⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧ ⟦S:AUTH-03|Access tokens expire within 15 minutes, and refresh tokens are rotated on use.⟧ ⟦S:AUTH-06|The login and token endpoints throttle or lock out repeated failed attempts.⟧

Authorization answers "what may this caller do?". ⟦S:AUTHZ-01|For every request touching a merchant-owned payment, the service verifies that the caller owns the payment or is entitled to it.⟧ ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧

## 5. Protecting card data

Card numbers are called PANs. ⟦S:CRYPTO-02|Primary account numbers are never stored in clear text and are tokenized by the card token vault.⟧ The merchant gets a token and we only keep the token and the last four digits.

About the rest of the data. ⟦F1|Encryption at rest is considered unnecessary for payments-db because the storage sits in a private network.⟧ The idea is that nobody from outside can reach the disk anyway.

 ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧ ⟦S:CRYPTO-07|Services validate TLS certificates and never disable verification.⟧

## 6. Personal data

 ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧ ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧

## 7. Secrets

⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧

## 8. Network and edge

⟦S:NET-01|payments-db and the Kafka brokers are in private subnets and are not publicly reachable.⟧ ⟦S:NET-05|External APIs sit behind a WAF with rate limiting.⟧ ⟦S:NET-04|The egress of services that call third parties is restricted to an approved allowlist.⟧

## 9. Input and output

⟦S:API-01|All external inputs are validated against a schema and rejected if invalid.⟧ ⟦S:API-04|Error responses do not reveal stack traces, SQL or internal hostnames.⟧ ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧ ⟦S:API-03|Webhook payloads, outbound and inbound, are signed and the signatures are verified.⟧

## 10. Logging

⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧

## 11. Build and operations

⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧ ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧

## 12. How a payment moves through the states

A new payment starts as created. After the acquirer approves the reservation it becomes authorized. A capture moves it to captured, and a refund moves it to refunded (partially or fully). If the acquirer declines, the payment becomes failed and nothing is reserved. Each change publishes an event, so the ledger and notification teams know what happened.

Idempotency is important: if the merchant backend repeats a request with the same reference and merchant_id because of a network error, the gateway returns the first payment and does not create a second one. A partial capture is allowed once, and the captured amount may never be larger than the authorized amount.

## 13. Open questions (TBD)

- What is the timeout for the acquirer call? Dana says 10 seconds; I need to check the acquirer contract.
- Should refunds be allowed after 90 days?
