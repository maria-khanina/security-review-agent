# Wallet Service - Design Document

Author: Andrei V., Wallet team
Status: Ready for review

## 1. Introduction

Wallet Service is the backend which keep the balance of customers and let them top up and send money to other wallets. The mobile application talk with the service only through Mobile API Gateway. This document describe the design, the data flow and the security controls. The OpenAPI file in the repository is the source of truth for the exact fields.

## 2. Components

- **Mobile API Gateway** - single entry for mobile traffic. It check the token with Keycloak and forward the request to wallet-core.
- **wallet-core** - the business logic: balances, top-ups, transfers, profile.
- **wallet-db (PostgreSQL)** - store balances, transactions and the profile of owner.
- **Keycloak** - identity provider for the customers.

## 3. Data flow

The mobile app send wallet and transfer requests to the gateway. The gateway ask Keycloak for token validation, and after it forward authenticated requests to wallet-core. Wallet-core read and write balances and transactions in wallet-db. There is no other path to the database.

## 4. API

- GET /v1/wallets/{walletId} - retrieve the wallet and balance (id, owner_name, balance, currency).
- POST /v1/wallets/{walletId}/topups - top up from a funding source (amount, funding_source_id); reply is a transaction with id, type, amount and created_at.
- POST /v1/transfers - transfer between two wallets (from_wallet_id, to_wallet_id, amount, note).
- GET /v1/wallets/{walletId}/transactions - list of the transactions of one wallet.
- PATCH /v1/wallets/{walletId}/profile - change owner_name, phone_number and address.

## 5. Authentication and authorization

Every externally reachable endpoint authenticate the caller with OAuth2 or OIDC bearer tokens, or with mutual TLS. The access token expire in 15 minutes at maximum and the refresh token is rotated on every use.

Customer passwords are stored only as salted hashes with argon2id or bcrypt, never in reversible form. The login and token endpoints do throttle or lock out the repeated failed attempts.

On every request for resource of a customer, the service verify that the caller is the owner or is entitled to the resource. Administrative and debug endpoints are not reachable from the public internet.

## 6. Data protection

Personally identifiable information is encrypted at rest with AES-256. The encryption keys are hold in KMS, never stored with the data which they protect, and rotated at least annually.

 Personal data may be sent to the third parties only under approved data processing agreement, and only the fields which are required. Non-production environments do not contain real personal or card data.

## 7. Transport, cryptography and edge

 The services validate TLS certificates and never disable the verification. Only the approved cryptographic algorithms are used, MD5, SHA-1, DES, 3DES and ECB mode are prohibited.

The database and message brokers are not publicly reachable and live in the private subnets. External APIs are placed behind a WAF with rate limiting. For the services which call third parties, the egress is restricted to approved allowlist.

## 8. Secrets

Secrets must not appear in the source code, configuration files, specifications or infrastructure definitions. The runtime secrets are fetched from the approved secret store when service starts.

## 9. Logging

Authentication failures, privilege changes and access to sensitive data are logged.

## 10. Application security

All external inputs are validated against a schema and rejected if they are invalid. Webhook payloads, outbound and inbound, are signed and the signatures are verified. The error responses do not reveal stack traces, SQL or internal hostnames. Database queries are parameterized and the concatenation of user input into queries is prohibited.

## 11. Operations

The CI scan the dependencies and images, and the critical vulnerabilities must be fixed within 14 days. Containers are running as non-root user, with read-only root filesystem where possible.

## 12. Behavior in details

A transfer is made in two steps. First the amount is reserved on the source wallet, second the amount is credited to the target wallet and the reservation is confirmed. If the service crash between the steps, a recovery job complete or cancel the transfer when it start again. The reference of the transfer is idempotent, so the same reference sent two times give back the first transaction.

A top-up is accepted with the status pending. When the funding source confirm the payment, the status is changed to completed and the balance is updated. If the funding source reject it, the status become failed and the balance is not changed.

Profile changes are applied immediately and the new values are returned in the reply.

## 13. Open points

- TBD: maximal amount of one transfer per day.
- TBD: texts of the error messages for the mobile team.
