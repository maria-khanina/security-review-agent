#wallet-design (pasted from slack, trimmed)

**[14:02] arjun:** for the wallet review doc, here's the thread, sorry for the mess

**[14:03] mei:** flow: mobile app -> mobile gateway -> keycloak (checks the caller) -> wallet-core -> wallet-db. wallet-core is "the core" in my messages, the doc should say wallet-core

**[14:05] mei:** endpoints: GET /v1/wallets/{walletId} (id, owner_name, balance, currency), POST .../topups (amount, funding_source_id), POST /v1/transfers (from_wallet_id, to_wallet_id, amount, note), GET .../transactions, PATCH .../profile (owner_name, phone_number, address)

**[14:09] arjun:** auth, from the meeting: ⟦S:AUTH-01|every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS⟧ , ⟦S:AUTH-03|access tokens expire within 15 minutes and refresh tokens are rotated on use⟧ , ⟦S:AUTH-05|customer passwords are stored only as salted hashes using argon2id or bcrypt, never in reversible form⟧ , ⟦S:AUTH-06|the login and token endpoints throttle or lock out repeated failed attempts⟧

**[14:09] arjun:** ⟦S:OPS-03|Backups are encrypted, and restores are tested at least twice a year.⟧

**[14:09] arjun:** ⟦S:CRYPTO-04|Traffic between services, and from services to data stores, is encrypted in transit.⟧

**[14:09] arjun:** ⟦S:AUTH-02|Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.⟧

**[14:11] priya:** and access: ⟦S:AUTHZ-01|for every request touching a customer-owned resource the service verifies that the caller owns it or is entitled to it⟧ , , ⟦S:AUTHZ-04|administrative and debug endpoints are not reachable from the public internet⟧

**[14:14] mei:** crypto: ⟦S:CRYPTO-01|personally identifiable information is encrypted at rest with AES-256⟧ , , ⟦S:CRYPTO-05|only approved cryptographic algorithms are used, MD5, SHA-1, DES, 3DES and ECB mode are prohibited⟧ , ⟦S:CRYPTO-06|encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually⟧ , ⟦S:CRYPTO-07|services validate TLS certificates and never disable verification⟧

**[14:14] mei:** ⟦S:SECRET-03|Rotation of service credentials happens every 90 days or sooner, and immediately after suspected exposure.⟧

**[14:14] mei:** ⟦S:CRYPTO-03|Clients outside our network must connect with TLS 1.2 or higher, and older protocol versions are refused.⟧

**[14:14] mei:** ⟦S:API-02|Each client is limited to 100 requests per minute, and requests above the limit receive HTTP 429.⟧

**[14:14] mei:** ⟦S:NET-05|The external API sits behind a WAF that also applies rate limiting.⟧

**[14:16] arjun:** secrets: ⟦S:SECRET-01|secrets do not appear in source code, configuration files, specifications or infrastructure definitions⟧ , ⟦S:SECRET-02|runtime secrets are fetched from the approved secret store at startup⟧ ,

**[14:18] priya:** network + edge: ⟦S:NET-01|wallet-db and the message brokers sit in private subnets and are not publicly reachable⟧ , , ⟦S:NET-04|services that call third parties have their egress restricted to an approved allowlist⟧ and yes the API enforces per-client rate limits

**[14:18] priya:** ⟦S:DATA-01|Each personal field we store is documented in the data inventory together with its purpose, and fields with no purpose are dropped.⟧

**[14:18] priya:** ⟦S:LOG-02|Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.⟧

**[14:21] mei:** logs: ⟦S:LOG-01|authentication failures, privilege changes and access to sensitive data are logged⟧ , . ⟦F3|wallet-core writes an audit entry for every balance-changing operation.⟧

**[14:23] arjun:** data: , , ⟦S:DATA-04|non-production environments do not contain real personal or card data⟧ . also ⟦F1|wallet-core calls the funding vendor to confirm every top-up.⟧

**[14:23] arjun:** ⟦S:LOG-04|Read access to the logging platform is granted per role: on-call engineers need it to find faults, security analysts need it to follow up alerts, and no other role is given access.⟧

**[14:23] arjun:** ⟦S:AUTHZ-03|Each service has a dedicated database account; this one is granted read access to the orders table and write access to its audit table only, since those are the only tables its functions touch.⟧

**[14:26] mei:** input/output: ⟦S:API-01|all external inputs are validated against a schema and rejected if invalid⟧ , ⟦F4|signature verification is skipped for the callbacks coming from the partner sandbox⟧ , ⟦S:API-04|error responses do not reveal stack traces, SQL or internal hostnames⟧ . for the transaction list ⟦F2|dynamic ordering uses the sort parameter directly in the SQL statement⟧ because the ORM could not express it

**[14:29] priya:** ops: ⟦S:OPS-01|the CI pipeline scans dependencies and images and critical vulnerabilities are fixed within 14 days⟧ , ⟦S:OPS-02|containers run as a non-root user with a read-only root filesystem where possible⟧ ,

**[14:31] arjun:** behavior section: transfers reserve on source then credit target then confirm, recovery job finishes or cancels after a crash, same reference twice returns the first transaction, topups are pending until the funding source confirms. TBD on the daily transfer cap

**[14:32] mei:** TBD on whether profile changes need a confirmation code
