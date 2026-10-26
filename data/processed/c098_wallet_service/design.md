# wallet design, thinking out loud

So the wallet service keeps the balances of the customer wallets and does top-ups, transfers and profile changes, and the mobile app talks to it only through the Mobile API Gateway, which I call the gateway or the edge dependending on who I talked to last, and the gateway asks Keycloak, the identity provider, to check the caller before forwarding to wallet-core, which I also write as the core or the wallet service, and wallet-core reads and writes wallet-db, the PostgreSQL with balances, transactions and the owner profile, and that is the whole picture, four boxes, and there is no other path to the database (TBD whether we draw Keycloak inside or outside the trust boundary on the diagram). The api has five calls, get a wallet (id, owner_name, balance, currency), top up (amount, funding_source_id), transfer (from_wallet_id, to_wallet_id, amount, note), list the transactions and patch the profile (owner_name, phone_number, address), and a transfer goes in two steps, first a reservation on the source wallet and then the credit on the target and a confirmation, with a recovery job that finishes or cancels a transfer if the core crashes in between, and the transfer reference makes the call idempotent so a retry returns the first transaction, and a top-up is pending until the funding source confirms and then completed or failed.

Now the security part, which I always forget to write unless somebody asks: every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS and for the passwords of customers passwords are stored only as salted hashes using argon2id or bcrypt and never in reversible form, and once the caller is in every request for a customer-owned resource verifies that the caller owns the resource or is entitled to it while administrative and debug endpoints are not reachable from the public internet and access reviews are done only when somebody leaves the company, which Lena owns I think. On the data, personally identifiable information is encrypted at rest with AES-256 and all external traffic uses TLS 1.2 or higher and only approved cryptographic algorithms are used and MD5, SHA-1, DES, 3DES and ECB mode are prohibited, and about what we keep and for how long, the service collects and stores only the personal data needed to operate wallets and and personal data is sent to third parties only under an approved data processing agreement and only the fields required, and reports and exports that contain personal data require authorization to access, are encrypted in storage and expire, which is about the finance csv that nobody remembers asking for.

Backups must be encrypted and restoration must be tested at least twice a year.

CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days.

We keep personal data for 12 months at most and delete it automatically when the period ends, or earlier on a verified request.

External APIs must sit behind a WAF with rate limiting.

In-transit encryption covers calls between services as well as connections to databases and queues.

Access token lifetime is capped at 15 minutes, and using a refresh token rotates it.

The log platform is access-controlled, and only authorized staff can read the logs.
Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year.

Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.

For the rest of the plumbing, secrets do not appear in source code, configuration files, specifications or infrastructure definitions and and wallet-db and the message brokers sit in private subnets and are not publicly reachable, and for the diary of the system authentication failures, privilege changes and access to sensitive data are logged and and, and on the input side all external inputs are validated against a schema and rejected if invalid and in the code database queries are parameterized and concatenating user input into queries is prohibited. The pipeline is and for the backups, and that leaves the open points, which are the maximum amount of a single transfer (TBD), whether a profile change needs a confirmation code (TBD), the page size of the transaction list, where support asked for fifty but the mobile team prefers twenty, and whether the core should cache balances for a second under heavy load, where finance says no and I tend to agree because a stale balance is the worst kind of bug in a wallet.

Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
Audit logs are tamper-evident and kept for at least a year.

Runtime secrets must be fetched from the approved secret store at startup.
