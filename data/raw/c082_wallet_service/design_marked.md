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

**Gateway.** ⟦F1|The Mobile API Gateway is the single entry point for all mobile traffic and forwards requests to wallet-core after it has talked to Keycloak.⟧ ⟦F2|The Mobile API Gateway runs as three replicas behind the cloud load balancer, and rolling updates replace one replica at a time.⟧

**Customers.** ⟦S:AUTH-05|Customer passwords are stored only as salted hashes using argon2id or bcrypt, never in reversible form.⟧ Mei checked the import path, ok.

**Access to data.**

**Crypto.** ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧ ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧

**Secrets.** ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧

**Network.**

**Logging.** ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧ ⟦S:LOG-02|Logs contain no secrets, card numbers or personal data beyond opaque identifiers.⟧

**Data.** ⟦S:DATA-02|Personal data has a defined retention period and is deleted when it expires or on a verified request from the data subject.⟧ Open: retention for transactions vs profile (TBD, legal says seven years for transactions). ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧

**Edge and input.** ⟦S:API-01|All external inputs are validated against a schema and rejected if invalid.⟧ ⟦S:API-06|Browser-facing APIs allow only approved origins in CORS.⟧ ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧

**Pipeline.** ⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧

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
