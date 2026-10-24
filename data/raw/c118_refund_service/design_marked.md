# Refund Service: Architecture Description

Author: Payments Platform (Marta H.)
Version: 1.0
Supersedes: the "Return Handler" note (the link to the old wiki no longer resolves)

## 1. Summary

The Refund Service lets merchants and support agents return money to a customer's card. It validates every request against the original payment, keeps the state of each refund, drives approvals and publishes status events for the ledger and the notification service. This document explains how the service is built and why, in enough detail for a new engineer to take it over.

## 2. Problem statement

Before this service, refunds were created by hand: a support agent opened the payment in the back office, calculated what was left to refund, entered the amount into the acquirer's portal and wrote a note on the ticket. This had three measurable problems. Handling time was high, mistakes happened when an agent refunded more than the remaining amount, and nobody could answer quickly how much had been refunded for a payment. The service automates the rules and gives one record of every refund.

## 3. Components

- **Refunds Gateway.** The public entry point for merchant integrations and the support console. It terminates TLS, forwards requests to refund-core and applies the limits configured for each client.
- **refund-core.** A stateless service with the business rules. It runs as three replicas and is configured through environment variables that name the other components.
- **refund-db (PostgreSQL).** The store of the service. It holds refund records with the reference of the original payment, the amount, the currency, the reason, the requester and the state, plus the approval history.
- **refund-events (Kafka).** The stream on which every change of state is published. The ledger and the notification service consume it.

Flows: merchant backends and support agents send requests to Refunds Gateway; the gateway sends authenticated requests to refund-core; refund-core reads and writes refund-db and publishes events to refund-events. There are no other flows. In particular refund-core does not call the card network itself; the return of the money is done by the acquirer connector of the payment service, which reads approved refunds from refund-events.

## 4. The API

All paths start with /v1.

1. POST /v1/refunds creates a refund. The request has payment_id, amount, currency, reason and requested_by. The response has id, payment_id, status, amount and currency.
2. GET /v1/refunds/{refundId} returns one refund with the same fields.
3. GET /v1/refunds lists refunds and can be filtered by status and payment_id.
4. POST /v1/refunds/{refundId}/approval approves or rejects a refund. The request has a decision and a comment.
5. POST /v1/refunds/{refundId}/cancellation cancels a refund that is still pending. The request has a reason.

## 5. Behavior in detail

Creation: the API checks that the payment exists, that it is captured, and that the new amount plus the refunds already made does not exceed the payment. If the amount is at or below the automatic limit, the refund is approved at once; otherwise it is pending and waits for a second person, who cannot be the requester. The refund then moves to approved, and the acquirer connector returns the money. When the connector reports success the refund becomes completed; if the card network refuses it, the refund becomes failed and the payments operations team picks it up.

Cancellation: only pending refunds can be cancelled. The reason is stored and a status event is published.

Ordering: refund-events has three partitions keyed by payment_id, so the events of one payment stay in order for the consumers. A consumer that sees a status twice must ignore the second occurrence; delivery is at least once.

## 6. Data model

refund-db has three tables. refund holds the refund records. approval holds one row for each decision with the approver, the decision, the comment and the time. outbox holds the events that have been written in the same transaction as the state change and not yet published. A small job moves rows from outbox to refund-events and marks them as sent, which is how the service avoids losing an event when the broker is unreachable.

## 7. Security design

7.1 Identity and access. ⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧ ⟦S:AUTHZ-01|Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.⟧ ⟦S:AUTHZ-04|Admin and debug endpoints are reachable only from the internal network, not from the public internet.⟧ ⟦S:AUTHZ-05|Access to production is recertified at least once per quarter.⟧

7.2 Card data and cryptography. ⟦S:CRYPTO-02|We do not keep primary account numbers: the card token vault tokenizes them and we store the token.⟧ ⟦S:CRYPTO-01|All personally identifiable information is encrypted before it lands on disk, using AES-256.⟧ ⟦S:CRYPTO-03|All external traffic uses TLS 1.2 or higher.⟧ ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧ The ownership of the keys and their rotation schedule are still to be written down (TBD with the platform team).

⟦S:SECRET-02|Runtime secrets are read from the secret store when the service starts.⟧

7.3 Secrets. ⟦S:SECRET-01|Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.⟧

⟦S:AUTH-02|Calls between our own services carry a signed workload identity token or use mutual TLS, and the receiving service checks it.⟧

7.4 Network and logging. ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧ ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧

7.5 Data protection. ⟦S:DATA-01|Only the personal data needed for the purpose is collected and stored.⟧ ⟦S:DATA-03|No personal data leaves for a third party without an approved DPA, and the payload is limited to the required fields.⟧ ⟦S:DATA-05|Download links for reports with personal data work for 24 hours, and the files are encrypted in storage and deleted after 7 days.⟧

7.6 Application. ⟦S:API-01|Schema validation runs on every external input, and invalid data never reaches the business logic.⟧ ⟦S:API-05|All queries use bound parameters instead of string concatenation.⟧

## 8. Failure handling

When refund-db is unreachable, refund-core returns an error and no state changes. When refund-events is unreachable, state changes are still committed together with their outbox rows, and the job publishes them when the broker is back; consumers may see a delay but not a loss. When the acquirer connector is unavailable, approved refunds wait in their state and are picked up when it returns. A refund that stays approved for more than one hour raises an alert to the payments on-call engineer.

## 9. Capacity

The peak is around forty refund requests a second during sale events and the average is below five. The service is sized for ten times the peak. Listing refunds is the most expensive operation; it uses an index on the payment reference and on the status, and it returns pages of at most one hundred records.

## 10. Rollout and open points

The service is released to a pilot group of merchants first, then to all merchants, and the manual process is retired in the third month. Open points: the exact automatic approval limit per merchant tier (TBD with Finance), the retention of approval history (TBD with the data protection officer), and whether merchants should receive a webhook for every status change or only for completed and failed refunds.
