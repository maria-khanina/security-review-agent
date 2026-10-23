#wallet-design (pasted from slack, trimmed)

**[14:02] arjun:** for the wallet review doc, here's the thread, sorry for the mess

**[14:03] mei:** flow: mobile app -> mobile gateway -> keycloak (checks the caller) -> wallet-core -> wallet-db. wallet-core is "the core" in my messages, the doc should say wallet-core

**[14:05] mei:** endpoints: GET /v1/wallets/{walletId} (id, owner_name, balance, currency), POST .../topups (amount, funding_source_id), POST /v1/transfers (from_wallet_id, to_wallet_id, amount, note), GET .../transactions, PATCH .../profile (owner_name, phone_number, address)

**[14:09] arjun:** auth, from the meeting: ⟦S:AUTH-01|every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS⟧ , ⟦S:AUTH-03|access tokens expire within 15 minutes and refresh tokens are rotated on use⟧ , ⟦S:AUTH-05|customer passwords are stored only as salted hashes using argon2id or bcrypt, never in reversible form⟧ , ⟦S:AUTH-06|the login and token endpoints throttle or lock out repeated failed attempts⟧

**[14:11] priya:** and access: ⟦S:AUTHZ-01|for every request touching a customer-owned resource the service verifies that the caller owns it or is entitled to it⟧ , , ⟦S:AUTHZ-04|administrative and debug endpoints are not reachable from the public internet⟧

**[14:14] mei:** crypto: ⟦S:CRYPTO-01|personally identifiable information is encrypted at rest with AES-256⟧ , , ⟦S:CRYPTO-05|only approved cryptographic algorithms are used, MD5, SHA-1, DES, 3DES and ECB mode are prohibited⟧ , ⟦S:CRYPTO-06|encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually⟧ , ⟦S:CRYPTO-07|services validate TLS certificates and never disable verification⟧

**[14:16] arjun:** secrets: ⟦S:SECRET-01|secrets do not appear in source code, configuration files, specifications or infrastructure definitions⟧ , ⟦S:SECRET-02|runtime secrets are fetched from the approved secret store at startup⟧ ,

**[14:18] priya:** network + edge: ⟦S:NET-01|wallet-db and the message brokers sit in private subnets and are not publicly reachable⟧ , , ⟦S:NET-04|services that call third parties have their egress restricted to an approved allowlist⟧ and yes ⟦F1|the API enforces per-client rate limits⟧

**[14:21] mei:** logs: ⟦S:LOG-01|authentication failures, privilege changes and access to sensitive data are logged⟧ , . ⟦F4|wallet-core writes an audit entry for every balance-changing operation.⟧

**[14:23] arjun:** data: , , ⟦S:DATA-04|non-production environments do not contain real personal or card data⟧ . also ⟦F2|wallet-core calls the funding vendor to confirm every top-up.⟧

**[14:26] mei:** input/output: ⟦S:API-01|all external inputs are validated against a schema and rejected if invalid⟧ , ⟦S:API-03|webhook payloads, outbound and inbound, are signed and the signatures are verified⟧ , ⟦S:API-04|error responses do not reveal stack traces, SQL or internal hostnames⟧ . for the transaction list ⟦F3|dynamic ordering uses the sort parameter directly in the SQL statement⟧ because the ORM could not express it

**[14:29] priya:** ops: ⟦S:OPS-01|the CI pipeline scans dependencies and images and critical vulnerabilities are fixed within 14 days⟧ , ⟦S:OPS-02|containers run as a non-root user with a read-only root filesystem where possible⟧ ,

**[14:31] arjun:** behavior section: transfers reserve on source then credit target then confirm, recovery job finishes or cancels after a crash, same reference twice returns the first transaction, topups are pending until the funding source confirms. TBD on the daily transfer cap

**[14:32] mei:** TBD on whether profile changes need a confirmation code
