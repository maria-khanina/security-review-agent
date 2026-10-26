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

- ⟦S:AUTH-01|No external endpoint serves anonymous traffic; callers present an OAuth2 token or a TLS client certificate.⟧
- ⟦S:NET-05|External APIs must sit behind a WAF with rate limiting.⟧
- ⟦S:OPS-01|CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧
- ⟦S:AUTHZ-01|Every request for a merchant-owned payment verifies that the caller owns the payment or is entitled to it.⟧
- ⟦S:SECRET-02|At startup the service fetches its secrets from the approved secret store.⟧
- ⟦S:LOG-03|Audit log entries are protected against silent modification and retained for a minimum of one year.⟧
- ⟦S:AUTH-02|Calls between our own services carry a signed workload identity token or use mutual TLS, and the receiving service checks it.⟧
- ⟦S:AUTHZ-04|Debug and administrative routes are not exposed to the internet.⟧
- ⟦F1|Access reviews for production are done only when someone leaves the company.⟧
- ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧
- ⟦S:CRYPTO-02|Primary account numbers are never stored in clear text and are tokenized by the card token vault.⟧
- ⟦S:DATA-02|Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.⟧
- ⟦S:CRYPTO-03|Clients outside our network must connect with TLS 1.2 or higher, and older protocol versions are refused.⟧
- ⟦S:CRYPTO-05|The approved algorithm list is followed, and MD5, SHA-1, DES, 3DES and ECB mode are prohibited in this service.⟧
- ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧
- ⟦S:OPS-03|We encrypt backups and run a restore test at least twice a year.⟧
- ⟦S:NET-01|payments-db and the Kafka brokers sit in private subnets and are not publicly reachable.⟧

### 6. Deployment

payments-core runs as four replicas behind the internal load balancer. Rolling updates replace one replica at a time.

---

## Part B (Mei, service side)

#### whats in the core

the core (payments-core, i also say "the payment service") owns the payment states: created, authorized, captured, refunded, failed. create is idempotent on reference + merchant_id so a retry gives back the first payment. partial capture allowed once, never above the authorized amount. refunds up to the captured amount, several partials ok. every state change goes out as an event on payment-events, at-least-once, consumers dedupe on payment id. The core runs as three replicas in our setup (platform half says four, check).

#### logging

- ⟦S:LOG-01|Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.⟧
- ⟦S:CRYPTO-06|KMS holds the keys, the data stores only keep ciphertext, and key rotation happens at least yearly.⟧

#### personal data

| area | rule |
|---|---|
| minimization | ⟦S:DATA-01|The gateway collects and stores only the personal data needed for payment processing.⟧ |
| third parties | ⟦S:DATA-03|No personal data leaves for a third party without an approved DPA, and the payload is limited to the required fields.⟧ |
| exports | ⟦S:DATA-05|Download links for reports with personal data work for 24 hours, and the files are encrypted in storage and deleted after 7 days.⟧

#### input, queries, build, backups

⟦S:API-01|Schema validation runs on every external input, and invalid data never reaches the business logic.⟧ ⟦S:API-05|We use parameterized queries only, with no SQL built from user input by string concatenation.⟧

⟦S:LOG-02|Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.⟧

#### acquirer

The connector calls the acquirer with a timeout. Part A has no value, the contract says fifteen seconds and an older note in the wiki says ten (the older note is outdated). A decline from the acquirer makes the payment failed and reserves nothing.

##### Differences between the halves

Part A says four replicas, Part B says three. Part A says "Payments Edge Gateway", Part B sometimes says "the PEG". Part A calls the topic payment-events, an older Part B note calls it "the payments bus". To be cleaned up before review.
