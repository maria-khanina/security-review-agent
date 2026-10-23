# Wallet Service Design

Assembled from: the wallet backend design (2021), the "mobile money" proposal (2022) and the identity migration notes (2023). Passages keep their original names; section 11 maps old names to current ones.

## 1. Background

The wallet backend (wallet-svc in the 2021 text, "money core" in the proposal, wallet-core today) holds the balance of each customer wallet and executes top-ups, transfers and profile changes. The mobile application reaches it through the Mobile API Gateway (called "mobile edge" in the proposal). The 2021 text described a monolithic application with a shared database; the current design separates the service and its own database, wallet-db.

## 2. Components

- **Mobile API Gateway**: single ingress for mobile traffic.
- **Keycloak**: identity provider (the 2021 text used a home-grown login service; it was retired in 2023).
- **wallet-core**: business rules.
- **wallet-db (PostgreSQL)**: balances, transactions and owner profile.

## 3. API

- GET /v1/wallets/{walletId}: id, owner_name, balance, currency.
- POST /v1/wallets/{walletId}/topups: amount, funding_source_id; returns id, type, amount, created_at.
- POST /v1/transfers: from_wallet_id, to_wallet_id, amount, note; returns the transaction.
- GET /v1/wallets/{walletId}/transactions: list.
- PATCH /v1/wallets/{walletId}/profile: owner_name, phone_number, address.

The 2021 text listed a sixth endpoint, DELETE /v1/wallets/{walletId}, which was removed when closing wallets became an operations task. Older clients that still call it receive not-found.

## 4. Authentication and authorization

This section replaces the 2021 and 2022 text. The earlier text used session cookies and later a shared API key; neither applies today.

⟦S:AUTH-01|Every request to an externally reachable endpoint is authenticated, either with an OIDC bearer token or with a mutual TLS client certificate.⟧ ⟦S:AUTH-03|A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use.⟧ ⟦S:AUTH-05|Passwords are stored only as salted argon2id hashes.⟧ ⟦S:AUTH-06|The login and token endpoints rate-limit failed attempts and lock the account after repeated failures.⟧

⟦S:AUTHZ-01|For every request touching a customer-owned resource, the service verifies that the caller owns the resource or is entitled to it.⟧ ⟦S:AUTHZ-04|The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.⟧

## 5. Data protection

⟦S:CRYPTO-01|Personal data is encrypted at rest with AES-256.⟧ ⟦S:CRYPTO-06|KMS holds the keys, the data stores only keep ciphertext, and key rotation happens at least yearly.⟧ ⟦S:CRYPTO-07|Services validate TLS certificates and never disable verification.⟧ ⟦S:CRYPTO-05|We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.⟧

 ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧ ⟦S:DATA-04|Test and staging environments use synthetic data, never real personal data or card data.⟧

## 6. Secrets, network and edge

⟦S:SECRET-01|Source, config, specs and infrastructure definitions contain no secrets.⟧ ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧

⟦S:NET-01|wallet-db and the message brokers sit in private subnets and are not publicly reachable.⟧ ⟦S:NET-05|Requests from the internet reach the API only through the WAF, where rate limits are enforced.⟧ ⟦S:NET-04|The service can reach only allow-listed third-party hosts, and all other outbound traffic is blocked.⟧

## 7. Input, errors and callbacks

⟦S:API-01|External inputs are accepted only if they validate against the schema.⟧ ⟦S:API-03|Webhook payloads, outbound and inbound, are signed and the signatures are verified.⟧ ⟦S:API-04|Internal details such as stack traces, SQL and hostnames never appear in an error response.⟧ ⟦S:API-05|User input reaches the database only as query parameters, never as part of the query text.⟧

## 8. Logging

⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are written to the logs.⟧

## 9. Build and operations

⟦S:OPS-01|Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks.⟧ ⟦S:OPS-02|No container runs as root, and the root filesystem is read-only wherever possible.⟧

wallet-core runs as three replicas. The 2021 text said two replicas plus a cold standby; the standby was dropped when the database moved to a managed service. Rolling updates replace one replica at a time. Builds ran on Jenkins in 2021; they run in the shared CI platform today.

## 10. Transfers

A transfer has two phases: reserve on the source wallet, then credit the target and confirm. A recovery job finishes or cancels a transfer interrupted by a crash. The transfer reference is idempotent, so the same reference submitted twice returns the first transaction. The proposal suggested a daily transfer limit of 1000; the current limit is set by product and is not stored in this document.

## 11. Name mapping

| Current name | 2021 name | Proposal name |
|---|---|---|
| wallet-core | wallet-svc | money core |
| Mobile API Gateway | api-gw | mobile edge |
| wallet-db | wallet schema in the shared database | ledger store |
| Keycloak | login-svc | identity service |

## 12. Open items

- Remove the leftover login-svc dashboards (see the old ticket, link may be dead).
- Update the runbook, which still shows two replicas.
