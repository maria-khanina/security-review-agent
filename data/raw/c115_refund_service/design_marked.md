# Refund Service: Architecture and Control Catalogue

Author: Anja K., Security Champion, Payments
Revision: 3 (revision 2 and the older "return handler" page are still linked from the wiki and partly outdated)
Review: Security Architecture

## 1. Summary

The Refund Service accepts requests to return money to a customer's card, validates them against the original payment, keeps the state of each refund and publishes status events. Merchants and support agents use it. Because it touches payments, the service is reviewed as part of the PCI scope. This document describes the architecture and then catalogues the security controls with identifiers that match the compliance tracker. The tracker holds the implementation status; the catalogue lists only what the design commits to.

## 2. Architecture

Merchant backends and support agents send refund requests to Refunds Gateway, which forwards authenticated requests to refund-core. refund-core applies the refund rules and stores each refund in refund-db (PostgreSQL), together with the reference of the original payment. Every change of state is published to refund-events (Kafka), which the ledger and the notification service consume.

The API has five operations under /v1:

- POST /v1/refunds creates a refund from payment_id, amount, currency, reason and requested_by and returns id, payment_id, status, amount and currency.
- GET /v1/refunds/{refundId} returns one refund.
- GET /v1/refunds lists refunds and can be filtered by status and payment_id.
- POST /v1/refunds/{refundId}/approval approves or rejects a refund (decision, comment).
- POST /v1/refunds/{refundId}/cancellation cancels a pending refund (reason).

## 3. Refund rules

The sum of the refunds of a payment may not exceed the amount of the payment. A refund is pending until it is approved; refunds below the automatic limit are approved on creation. A refund can be cancelled while pending. After approval the money is returned through the acquirer connector of the payment service, and the refund becomes completed or failed. Failed refunds are reviewed by the payments operations team.

## 4. Control catalogue

Identifiers (R-1 and so on) match the compliance tracker. The "return handler" page used a different numbering and should not be used.

### 4.1 Identity and access

- R-1: ⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧
- R-2: ⟦F2|refund-core receives each request from Refunds Gateway together with the identity of the calling client or agent.⟧
- R-3: ⟦S:AUTHZ-01|Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.⟧
- R-4: ⟦S:AUTHZ-04|Nothing administrative or meant for debugging can be called from outside our network.⟧
- R-5: ⟦S:AUTHZ-05|Production access rights are reviewed every quarter.⟧

### 4.2 Data and cryptography

- R-6: ⟦F1|The full card number is kept with the payment record and returned in the API response, so that merchants can reconcile refunds against their own books.⟧
- R-7: ⟦S:CRYPTO-01|Stored PII is protected with AES-256 encryption or stronger.⟧
- R-8: ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
- R-9: ⟦S:DATA-01|Only the personal data needed for the purpose is collected and stored.⟧
- R-10: ⟦S:DATA-03|Third parties receive only the fields they need, and only if an approved data processing agreement covers them.⟧
- R-11: ⟦S:DATA-05|Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.⟧

⟦S:CRYPTO-03|All public-facing endpoints terminate TLS 1.2 or higher.⟧
⟦S:LOG-04|The log platform is access-controlled, and only authorized staff can read the logs.⟧

⟦S:AUTH-02|We do not trust the internal network by itself: every internal call is authenticated with mTLS or workload identity tokens.⟧

### 4.3 Transport, secrets and network

- R-12: All traffic is served over HTTPS only.
- R-13: ⟦S:SECRET-01|Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.⟧

⟦S:SECRET-02|Runtime secrets must be fetched from the approved secret store at startup.⟧
- R-14: ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧

### 4.4 Logging and application security

- R-15: ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are written to the logs.⟧
- R-16: ⟦S:API-01|Schema validation runs on every external input, and invalid data never reaches the business logic.⟧
- R-17: ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧

## 5. Deployment and capacity

refund-core is stateless and runs as three replicas behind the internal load balancer (revision 2 said two). Refunds Gateway is the only component with a public address. The peak is around forty refund requests a second during sale events; the database is sized for ten times that. refund-events has three partitions keyed by payment_id so that the events of one payment stay in order.

## 6. Observability

One dashboard per environment shows requests, refund states and the age of the oldest pending refund. An alert fires when a refund is pending longer than the threshold in the runbook. The payments on-call rota receives the alerts. The runbook is in the payments space (the link to the old space may not work).

## 7. Known gaps

The catalogue has no implementation status column; the tracker carries it. The retention period for completed refund records is not decided. The sections of revision 1 about manual refunds by e-mail are kept in the archive and are not repeated here.
