# Wallet Service Design

## Part A (Arjun, platform side)

### 1. Overview

The Wallet Service keeps the balance of each customer wallet and lets customers top up and send money to other wallets. The mobile application reaches it only through the Mobile API Gateway.

### 2. Components

- Mobile API Gateway: single ingress for mobile traffic.
- Keycloak: identity provider for customers; the gateway asks it to validate every token.
- wallet-core: balances, top-ups, transfers and profile.
- wallet-db (PostgreSQL): balances, transactions and owner profile.

### 3. Data flow

The mobile app sends wallet and transfer requests to the gateway. The gateway asks Keycloak for token validation and then forwards authenticated requests to wallet-core. wallet-core reads and writes balances and transactions in wallet-db. There is no other path to the database.

### 4. API

- GET /v1/wallets/{walletId} returns id, owner_name, balance and currency.
- POST /v1/wallets/{walletId}/topups takes amount and funding_source_id and returns a transaction (id, type, amount, created_at).
- POST /v1/transfers takes from_wallet_id, to_wallet_id, amount and note and returns a transaction.
- GET /v1/wallets/{walletId}/transactions lists transactions.
- PATCH /v1/wallets/{walletId}/profile changes owner_name, phone_number or address.

### 5. Security (platform view)

The API authenticates callers with JWT bearer tokens. All traffic is served over HTTPS only.

 The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.

Personally identifiable information is encrypted at rest with AES-256. Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.

All public-facing endpoints terminate TLS 1.2 or higher.

Public API traffic passes through a web application firewall with rate limits.

Traffic between services, and from services to data stores, is encrypted in transit.

Each service must use its own database account with the minimum grants and no shared administrative credentials.
Data stores and brokers sit in private subnets only.

Service-to-service calls are authenticated, either with mutual TLS between the workloads or with a signed workload identity token.

Credentials are never committed to code, configuration, specifications or infrastructure-as-code files. On boot, the service pulls its credentials from the approved secret store.

Encrypted backups are checked by a restoration exercise at least twice a year.

### 6. Deployment

wallet-core runs as three replicas behind the internal load balancer. Rolling updates replace one replica at a time.

---

## Part B (Mei, backend side)

#### What the wallet "core" does

The core (that is wallet-core, sometimes I say the wallet service) does the money maths. For a transfer it first reserves the money on the sender, then credits the receiver, then confirms. wallet-core takes the list and search parameters of the transaction calls and turns them into the lookups it needs. If something crashes in the middle a recovery job finishes or cancels the transfer. Core runs as two replicas in our setup (the platform half says three, we should align).

#### Logging

Privilege changes are made by administrators directly in the database and leave no trace. Logs carry opaque identifiers only and never include secrets, card numbers or personal data.

The API enforces a limit of 300 requests per minute for each client and answers HTTP 429 when it is exceeded.

Workloads are non-root, and read-only root filesystems are used wherever they can be.

#### Passwords and login

Customers log in through Keycloak. About password storage in the legacy import: a fast hash with a single global salt is used for passwords. We kept that from the old system so migrated customers can still log in without a reset.

#### Browser access

The web wallet calls the gateway from the browser. Allowed origins are not configured; the gateway reflects the request origin. This made the web team's life easier during development.

#### Data handling

| topic | rule |
|---|---|
| retention | Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends. |
| third parties | Customer data is already shared with a new provider while the contract with them is still being negotiated. |
| input | Schema validation runs on every external input, and invalid data never reaches the business logic.

**Rate limits**

#### Pipeline

CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days.

#### Behavior notes

A top-up starts as pending and becomes completed when the funding source confirms it, or failed when it is rejected. A transfer reference makes the call idempotent: the same reference sent twice returns the first transaction. Profile changes apply immediately. The transactions list is newest first and pages with a token.

##### Differences between the halves

Part A says the gateway forwards to three replicas, Part B says two. Part A calls the database "wallet-db", Part B sometimes says "the ledger db" (it is the same database, there is no separate ledger). To be cleaned up before review.
