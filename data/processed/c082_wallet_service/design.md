# wallet service design review (notes)

Attendees: Arjun, Mei, Tomas, Priya
Notes: Tomas

## overview

Wallet backend: keeps balances, does top-ups, transfers and profile changes. Mobile app reaches it through the Mobile API Gateway (a.k.a. "the gateway", "mobile edge" on Priya's slides, let's settle on Mobile API Gateway). Behind it: wallet-core (also "the core"), wallet-db (PostgreSQL) and Keycloak for customer accounts.

## API (from the openapi file)

- GET /v1/wallets/{walletId}: id, owner_name, balance, currency
- POST /v1/wallets/{walletId}/topups: amount, funding_source_id -> transaction
- POST /v1/transfers: from_wallet_id, to_wallet_id, amount, note -> transaction
- GET /v1/wallets/{walletId}/transactions: list
- PATCH /v1/wallets/{walletId}/profile: owner_name, phone_number, address

## discussion

**Gateway.** The Mobile API Gateway is the single entry point for all mobile traffic and forwards requests to wallet-core after it has talked to Keycloak. The Mobile API Gateway runs as three replicas behind the cloud load balancer, and rolling updates replace one replica at a time.

All public-facing endpoints terminate TLS 1.2 or higher.

**Customers.** Customer passwords are stored only as salted hashes using argon2id or bcrypt, never in reversible form. Mei checked the import path, ok.

The database account of the service has the minimum grants its functions need: reads on two tables and writes on one, and the administrative credentials are held by the database team alone.
Neither the database nor the broker has a public endpoint, and both live in private subnets.

**Access to data.**

**Crypto.** Personally identifiable information is encrypted at rest with AES-256. Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.

**Secrets.** Secrets do not appear in source code, configuration files, specifications or infrastructure definitions. The approved secret manager is the only source of runtime secrets, fetched at start-up.

A WAF with rate limiting protects the externally exposed API.

Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.

**Network.**

**Logging.** Authentication failures, privilege changes and access to sensitive data are written to the logs. Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids.

**Data.** Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job. Open: retention for transactions vs profile (TBD, legal says seven years for transactions). Third parties receive only the fields they need, and only if an approved data processing agreement covers them.

**Edge and input.** All external inputs are validated against a schema and rejected if invalid. The allow-list of origins in the gateway is empty, and the gateway treats an empty list as allow everything. We use parameterized queries only, with no SQL built from user input by string concatenation.

**Pipeline.** Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks.

Workloads are non-root, and read-only root filesystems are used wherever they can be.

## behavior notes

- Transfer: reserve on source, credit target, confirm. Recovery job finishes or cancels after a crash.
- Same transfer reference twice returns the first transaction.
- Top-up is pending until the funding source confirms, then completed or failed.
- Profile changes apply immediately.

## action items

- Arjun: confirm the replica count of the gateway (TBD).
- Priya: decide on the daily transfer cap with product.
- Tomas: write up the retention decision once legal answers.
- Mei: update the diagram (still shows the old login service).
