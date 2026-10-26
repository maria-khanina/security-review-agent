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

In a gateway, authentication answers "who is calling?". Public endpoints reject any call that carries neither a valid OAuth2 bearer token nor a client certificate. Tokens are short-lived (15 minutes maximum) and refresh tokens are single-use, so each refresh issues a new one. Repeated failed logins are slowed down, and ten consecutive failures trigger a temporary lockout of the account.

Rotation of service credentials happens every 90 days or sooner, and immediately after suspected exposure.

The API enforces a limit of 300 requests per minute for each client and answers HTTP 429 when it is exceeded.

In-transit encryption covers calls between services as well as connections to databases and queues.

Authorization answers "what may this caller do?". For every request touching a merchant-owned payment, the service verifies that the caller owns the payment or is entitled to it. The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.

## 5. Protecting card data

Card numbers are called PANs. Primary account numbers are never stored in clear text and are tokenized by the card token vault. The merchant gets a token and we only keep the token and the last four digits.

About the rest of the data. Encryption at rest is considered unnecessary for payments-db because the storage sits in a private network. The idea is that nobody from outside can reach the disk anyway.

 Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned. Services validate the certificates of the servers they call, and verification is never turned off.

The service stores only the personal fields that appear in its data inventory with a stated purpose.

## 6. Personal data

 No personal data leaves for a third party without an approved DPA, and the payload is limited to the required fields. Developers copy production payment data to their laptops when they need to reproduce a bug.

All public-facing endpoints terminate TLS 1.2 or higher.

## 7. Secrets

No secrets are kept in source code, config files, API specs or infrastructure definitions. Runtime secrets are read from the secret store when the service starts.

## 8. Network and edge

payments-db and the Kafka brokers are in private subnets and are not publicly reachable. Requests from the internet reach the API only through the WAF, where rate limits are enforced. The egress of services that call third parties is restricted to an approved allowlist.

Service-to-service calls are authenticated, either with mutual TLS between the workloads or with a signed workload identity token.

## 9. Input and output

Schema validation runs on every external input, and invalid data never reaches the business logic. Error responses do not expose stack traces, SQL or internal hostnames. Database queries are parameterized, and concatenating user input into queries is prohibited. Webhook payloads are HMAC-signed and timestamped, and the receiver verifies the signature and the timestamp before accepting them.

The retention period is 24 months for customer records and 90 days for delivery logs, and expired data is removed by a scheduled deletion job.

Only authorized staff can access the central logs.

## 10. Logging

The audit trail includes authentication failures, privilege changes and sensitive-data access.

## 11. Build and operations

The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days. The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only.

Audit log entries are protected against silent modification and retained for a minimum of one year.

## 12. How a payment moves through the states

A new payment starts as created. After the acquirer approves the reservation it becomes authorized. A capture moves it to captured, and a refund moves it to refunded (partially or fully). If the acquirer declines, the payment becomes failed and nothing is reserved. Each change publishes an event, so the ledger and notification teams know what happened.

Idempotency is important: if the merchant backend repeats a request with the same reference and merchant_id because of a network error, the gateway returns the first payment and does not create a second one. A partial capture is allowed once, and the captured amount may never be larger than the authorized amount.

## 13. Open questions (TBD)

- What is the timeout for the acquirer call? Dana says 10 seconds; I need to check the acquirer contract.
- Should refunds be allowed after 90 days?
