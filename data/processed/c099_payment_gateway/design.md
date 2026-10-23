# Payment Gateway Design

## Part A (Arjun, platform side)

### 1. Overview

The Payment Gateway accepts card payments from merchants, routes them to the acquiring banks and publishes payment events. Merchants send a card token and never a card number.

### 2. Components

- Payments Edge Gateway: single public ingress.
- payments-core: payment state machine and business rules.
- payments-db (PostgreSQL): payment records.
- Acquirer connector: adapter to the acquiring bank.
- payment-events (Kafka): status events for other teams.

### 3. Data flow

The merchant backend sends a payment request with a card token to the edge gateway. The gateway forwards the validated request to payments-core. payments-core writes the payment to payments-db, sends an authorization request to the acquirer through the connector and publishes status events on payment-events.

### 4. API

- POST /v1/payments creates a payment (amount, currency, card_token, merchant_id, reference).
- GET /v1/payments/{paymentId} returns a payment.
- POST /v1/payments/{paymentId}/capture captures an authorized payment (amount).
- POST /v1/payments/{paymentId}/refunds refunds a payment (amount, reason).
- GET /v1/payments lists payments.

Payment replies carry id, status, amount, currency, last4 and merchant_id.

### 5. Security (platform controls)

- Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.
- Every request for a merchant-owned payment verifies that the caller owns the payment or is entitled to it.
- Administrative and debug endpoints are not reachable from the public internet.
- Access rights to production systems are reviewed at least quarterly.
- Personally identifiable information is encrypted at rest with AES-256.
- Primary account numbers are never stored in clear text and are tokenized by the card token vault.
- All external traffic uses TLS 1.2 or higher.
- Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- payments-db and the Kafka brokers sit in private subnets and are not publicly reachable.

### 6. Deployment

payments-core runs as four replicas behind the internal load balancer. Rolling updates replace one replica at a time.

---

## Part B (Mei, service side)

#### whats in the core

the core (payments-core, i also say "the payment service") owns the payment states: created, authorized, captured, refunded, failed. create is idempotent on reference + merchant_id so a retry gives back the first payment. partial capture allowed once, never above the authorized amount. refunds up to the captured amount, several partials ok. every state change goes out as an event on payment-events, at-least-once, consumers dedupe on payment id. The core runs as three replicas in our setup (platform half says four, check).

#### logging

- Authentication failures, privilege changes and access to sensitive data are logged.

#### personal data

| area | rule |
|---|---|
| minimization | The gateway collects and stores only the personal data needed for payment processing. |
| third parties | Personal data is sent to third parties only under an approved data processing agreement, and only the fields required. |
| exports | Reports and exports that contain personal data require authorization to access, are encrypted in storage and expire.

#### input, queries, build, backups

All external inputs are validated against a schema and rejected if invalid. Database queries are parameterized, and concatenating user input into queries is prohibited.

#### acquirer

The connector calls the acquirer with a timeout. Part A has no value, the contract says fifteen seconds and an older note in the wiki says ten (the older note is outdated). A decline from the acquirer makes the payment failed and reserves nothing.

##### Differences between the halves

Part A says four replicas, Part B says three. Part A says "Payments Edge Gateway", Part B sometimes says "the PEG". Part A calls the topic payment-events, an older Part B note calls it "the payments bus". To be cleaned up before review.
