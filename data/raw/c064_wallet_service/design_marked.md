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

⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧ ⟦S:AUTH-03|Access tokens expire within 15 minutes, and refresh tokens are rotated on use.⟧ ⟦S:AUTH-05|Customer passwords are stored only as salted hashes using argon2id or bcrypt, never in reversible form.⟧ ⟦S:AUTH-06|The login and token endpoints throttle or lock out repeated failed attempts.⟧

⟦S:AUTHZ-01|For every request touching a customer-owned resource, the service verifies that the caller owns the resource or is entitled to it.⟧ ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧

## 5. Data protection

⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧ ⟦S:CRYPTO-06|Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.⟧ ⟦S:CRYPTO-07|Services validate TLS certificates and never disable verification.⟧ ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧

 ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧ ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧

## 6. Secrets, network and edge

⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧

⟦S:NET-01|wallet-db and the message brokers sit in private subnets and are not publicly reachable.⟧ ⟦S:NET-05|External APIs sit behind a WAF with rate limiting.⟧ ⟦S:NET-04|Services that call third parties have their egress restricted to an approved allowlist.⟧

## 7. Input, errors and callbacks

⟦S:API-01|All external inputs are validated against a schema and rejected if invalid.⟧ ⟦S:API-03|Webhook payloads, outbound and inbound, are signed and the signatures are verified.⟧ ⟦S:API-04|Error responses do not reveal stack traces, SQL or internal hostnames.⟧ ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧

## 8. Logging

⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧

## 9. Build and operations

⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧ ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧

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
