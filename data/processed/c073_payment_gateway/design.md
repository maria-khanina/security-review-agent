# Payment Gateway: Architecture and Security Control Catalogue

Author: Rina M., Security Champion, Payments Platform
Review: Security Architecture
Revision: 7 (revision 6 called the front component "Edge-GW"; the name is retired but still appears in two dashboards)

## 1. Summary

The Payment Gateway accepts card payments from merchants, routes them to acquiring banks and publishes payment events. Because it sits on the path of every payment, its controls are catalogued here in detail. Reviewers should read the control catalogue (section 5) first and the architecture afterwards.

## 2. Architecture

Merchant backends call the Payments Edge Gateway with a payment request that carries a card token. The gateway forwards validated requests to payments-core. payments-core stores payment records in payments-db (PostgreSQL), sends authorization requests to the acquirer through the Acquirer connector and publishes status events on payment-events (Kafka).

payments-core is the central service of the gateway: it owns the payment state machine and coordinates the database, the acquirer connector and the event stream. payments-core signs and protects the messages it exchanges with the acquirer and with the event stream.

## 3. API

- POST /v1/payments creates a payment (amount, currency, card_token, merchant_id, reference) and returns id, status, amount, currency, last4 and merchant_id.
- GET /v1/payments/{paymentId} returns one payment.
- POST /v1/payments/{paymentId}/capture captures an authorized payment (amount).
- POST /v1/payments/{paymentId}/refunds refunds a payment (amount, reason) and returns id, status and amount.
- GET /v1/payments lists payments.

A payment moves through created, authorized, captured and refunded, or ends in failed after a decline. Creation is idempotent on the reference together with the merchant identifier.

## 4. Reporting

Finance receives settlement reports as files. The reports are produced by a nightly job that writes CSV files to a storage bucket and notifies finance when they are ready.

## 5. Control catalogue

Control identifiers (P-1 and so on) match the compliance spreadsheet (link TBD; the spreadsheet under the previous team name is stale).

### 5.1 Identity and access

- P-1: Callers authenticate with OAuth2 bearer tokens.
- P-3: Admin and debug endpoints are reachable only from the internal network, not from the public internet.

Every build scans libraries and container images, and critical vulnerabilities get a 14-day fix deadline.
- P-4: A quarterly access review covers all production systems.

Any authenticated caller can read any payment record if it knows the payment identifier.

### 5.2 Data protection

- P-6: All external traffic uses TLS 1.2 or higher.

No external endpoint serves anonymous traffic; callers present an OAuth2 token or a TLS client certificate.
- P-7: The gateway collects and stores only the personal data needed for payment processing.

Log lines are kept free of secrets, card numbers and personal details, and identifiers are opaque.

Access to centralized logs must be limited to authorized staff.
- P-9: Personal data goes to third parties only under an approved data processing agreement, and only the required fields are sent.

All external inputs must be validated against a schema and rejected if invalid.
Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- P-10: Report files remain in the storage bucket and are never deleted.

Audit log entries are protected against silent modification and retained for a minimum of one year.

### 5.3 Secrets and network

- P-11: Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- P-13: payments-db and the Kafka brokers sit in private subnets and are not publicly reachable.

### 5.4 Logging

- P-14: The audit trail includes authentication failures, privilege changes and sensitive-data access.

On boot, the service pulls its credentials from the approved secret store.

### 5.5 Application security

- P-17: Requests are validated against strict schemas.
- P-18: Database queries are parameterized, and user input is never concatenated into SQL.

The external API sits behind a WAF that also applies rate limiting.

The internal services call each other with one long-lived token that every service reuses.

### 5.6 Operations

## 6. Capacity and deployment

The gateway handles several hundred authorization requests per second at peak. payments-core is stateless and runs as four replicas behind the internal load balancer (revision 6 said three; four is correct); the database primary is the single writer with a standby in a second availability zone. Deployments are rolling with a small canary for fifteen minutes. The acquirer connector retries failed calls with growing delays and surfaces a failed payment when the acquirer stays unavailable.

## 7. Events

Every state change publishes an event on payment-events with at-least-once delivery. Consumers, for example ledger and notifications, de-duplicate on the payment identifier. Events carry identifiers and amounts and no card data.

## 8. Open items

- Status column of the catalogue: the controls are listed without an implementation status; the spreadsheet carries it (link TBD).
- Acquirer timeout: ten or fifteen seconds is still being agreed with the acquirer (TBD).
- Reference to the architecture of revision 1 lives in the archived wiki and may not open.
