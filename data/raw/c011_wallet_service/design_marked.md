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

⟦S:AUTH-01|Public endpoints reject any call that carries neither a valid OAuth2 bearer token nor a client certificate.⟧ ⟦S:AUTH-03|The access token expire in 15 minutes at maximum and the refresh token is rotated on every use.⟧

⟦S:DATA-02|The retention period is 24 months for customer records and 90 days for delivery logs, and expired data is removed by a scheduled deletion job.⟧

⟦S:LOG-02|Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.⟧

⟦S:AUTH-05|Passwords are stored only as salted argon2id hashes.⟧ ⟦S:AUTH-06|The login and token endpoints throttle repeated failures and apply a temporary lockout once an account reaches ten consecutive failed attempts.⟧

⟦S:DATA-05|Each export file is encrypted at rest, readable only by the authorized requester, and removed automatically after 72 hours.⟧

⟦S:AUTHZ-01|On every request for resource of a customer, the service verify that the caller is the owner or is entitled to the resource.⟧ ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧

## 6. Data protection

⟦S:CRYPTO-01|At rest, personal data is protected with AES-256 in both the database and object storage, with keys from the corporate key management service.⟧ ⟦S:CRYPTO-06|Key material is kept in KMS and separate from the data, and keys are rotated every year or sooner.⟧

 ⟦S:DATA-03|Personal data goes to third parties only under an approved data processing agreement, and only the required fields are sent.⟧ ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧

## 7. Transport, cryptography and edge

 ⟦S:CRYPTO-07|The services validate TLS certificates and never disable the verification.⟧ ⟦S:CRYPTO-05|We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.⟧

⟦S:AUTHZ-03|Each service has a dedicated database user limited to the tables and operations it uses, and administrative credentials are not shared.⟧

⟦S:NET-01|The database and the message broker are in private subnets with no public address.⟧ ⟦S:NET-05|A WAF with rate limiting protects the externally exposed API.⟧ ⟦S:NET-04|For the services which call third parties, the egress is restricted to approved allowlist.⟧

## 8. Secrets

⟦S:SECRET-01|Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.⟧ ⟦S:SECRET-02|The runtime secrets are fetched from the approved secret store when service starts.⟧

## 9. Logging

⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧

## 10. Application security

⟦S:API-01|All external input is validated against a schema, and invalid requests are rejected.⟧ ⟦S:API-03|Every webhook we send or receive is signed with an HMAC, and the receiver checks the signature together with the timestamp.⟧ ⟦S:API-04|Internal details such as stack traces, SQL and hostnames never appear in an error response.⟧ ⟦S:API-05|Database queries are parameterized and the concatenation of user input into queries is prohibited.⟧

⟦S:CRYPTO-04|In-transit encryption covers calls between services as well as connections to databases and queues.⟧

## 11. Operations

⟦S:OPS-01|CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧ ⟦S:OPS-02|Containers are running as non-root user, with read-only root filesystem where possible.⟧

⟦S:LOG-04|Only authorized staff can access the central logs.⟧

## 12. Behavior in details

A transfer is made in two steps. First the amount is reserved on the source wallet, second the amount is credited to the target wallet and the reservation is confirmed. If the service crash between the steps, a recovery job complete or cancel the transfer when it start again. The reference of the transfer is idempotent, so the same reference sent two times give back the first transaction.

A top-up is accepted with the status pending. When the funding source confirm the payment, the status is changed to completed and the balance is updated. If the funding source reject it, the status become failed and the balance is not changed.

Profile changes are applied immediately and the new values are returned in the reply.

## 13. Open points

- TBD: maximal amount of one transfer per day.
- TBD: texts of the error messages for the mobile team.
