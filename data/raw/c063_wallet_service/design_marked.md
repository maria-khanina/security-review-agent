# Wallet Service: Architecture and Design Rationale

Author: Elena R., Principal Architect, Wallet Platform
Status: Approved by Architecture Board

## 1. Context and goals

The Wallet Service holds the balance of every customer wallet and executes top-ups, transfers and profile changes. It is the system that customers feel most directly: if it is slow or wrong, the product is slow or wrong. The goals, in order of priority, are correctness of balances, availability of the mobile path, a small and auditable operational surface, and ease of evolution.

## 2. Architecture overview

The design has four parts.

1. **Mobile API Gateway**, the single ingress for mobile traffic and, as explained in section 6, for a few other callers.
2. **Keycloak**, the identity provider for customers. The gateway asks it to validate every token.
3. **wallet-core**, which implements the business rules: balances, top-ups, transfers and profile.
4. **wallet-db (PostgreSQL)**, the datastore for balances, transactions and owner profiles.

Requests travel from the mobile application to the gateway, from the gateway to Keycloak for token validation, and then, as authenticated requests, to wallet-core. wallet-core reads and writes balances and transactions in wallet-db. There is no other path to wallet-db.

⟦F1|wallet-db (PostgreSQL) is the system of record for every balance, transaction and owner profile, and it runs as a primary with a standby in a second availability zone.⟧

## 3. API

- GET /v1/wallets/{walletId} returns the wallet (id, owner_name, balance, currency).
- POST /v1/wallets/{walletId}/topups takes amount and funding_source_id and returns a transaction (id, type, amount, created_at).
- POST /v1/transfers takes from_wallet_id, to_wallet_id, amount and note and returns a transaction.
- GET /v1/wallets/{walletId}/transactions lists the wallet's transactions.
- PATCH /v1/wallets/{walletId}/profile changes owner_name, phone_number or address and returns the wallet.

Card numbers are never returned by the API. When a customer adds a card as a funding source, the application only ever receives the funding source identifier afterwards.

## 4. Identity and access

⟦S:AUTH-01|Public endpoints reject any call that carries neither a valid OAuth2 bearer token nor a client certificate.⟧

⟦F3|Passwords are hashed with plain SHA-256, without a per-user salt.⟧

⟦S:AUTHZ-01|For every request touching a customer-owned resource, the service verifies that the caller owns the resource or is entitled to it.⟧ The check is performed in wallet-core and not in the gateway, because wallet-core is the only component that knows the wallet's owner.

⟦S:AUTHZ-05|Access to production is recertified at least once per quarter.⟧

## 5. Transport, secrets and network

⟦S:CRYPTO-03|External traffic is served over TLS 1.2 or newer.⟧ ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧

⟦S:SECRET-02|Runtime secrets are read from the secret store when the service starts.⟧

⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧

⟦S:NET-01|wallet-db and the message brokers sit in private subnets and are not publicly reachable.⟧
⟦S:AUTH-02|Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.⟧

## 6. Operations access

Support and operations staff need to change limits and inspect wallets. The architecture board considered a separate internal gateway and rejected it for the first release on grounds of cost and delay. ⟦F2|Admin routes are served by the same public gateway as customer routes, for example PUT /admin/limits/{accountId} for the limits override.⟧ Access to those routes is controlled by roles in the identity provider.

## 7. Data handling

⟦S:DATA-01|The service collects and stores only the personal data needed to operate wallets.⟧ ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧

## 8. Input handling and queries

⟦S:API-01|External inputs are accepted only if they validate against the schema.⟧ ⟦S:API-05|We use parameterized queries only, with no SQL built from user input by string concatenation.⟧

## 9. Logging

⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧

## 10. Build, run and recover

wallet-core is stateless and scales horizontally behind the gateway; the database primary is the single writer. Deployments are rolling with a small canary share for fifteen minutes before the rest is updated, and rollback is automatic when the error rate crosses the agreed threshold. The recovery objective for a regional failure is two hours, exercised in a quarterly game day.

## 11. Transfers

A transfer is a two-phase operation. wallet-core first reserves the amount on the source wallet, then credits the target wallet and confirms the reservation. A crash between the phases is resolved by a recovery job that completes or cancels the transfer when the service restarts. The transfer reference is idempotent: the same reference submitted twice returns the first transaction. A top-up starts as pending and becomes completed when the funding source confirms it, or failed when it is rejected.

## 12. Risks and follow-ups

- The decision to share the gateway with operations access will be revisited once the volume of support overrides is known.
- Ownership of the key ceremony for the platform keys is being clarified (TBD).
- The list of roles for operations is under review with Security (TBD).
