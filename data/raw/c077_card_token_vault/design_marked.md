# CTV infra (terse)

Assumes the usual platform setup unless a line says otherwise. Old page: wiki/CTV-v1 (moved, ask Lena).

## shape

- payment svcs -> tokenization-service (tokenize PAN->token, detokenize token->PAN w/ purpose code)
- tokenization-service -> vault-db (PG) for encrypted records, -> Vault+KMS for DEKs
- all inside the vault private subnet

## tf

- kms `vault_key`
- rds `vault_db` (card_data)
- sg `vault_db_sg`
- loggroup `vault_audit`
- backup_vault `vault_backups`
- iam `vault_service_policy`

## authN/Z

- ⟦F1|The internal endpoints of the tokenization-service are protected only by URL paths that are not published anywhere.⟧
- ⟦S:CRYPTO-04|Traffic between services and to data stores must be encrypted in transit.⟧
- ⟦S:LOG-02|Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids.⟧
- ⟦S:API-01|Requests from outside are checked against the schema and rejected if they do not conform.⟧
- ⟦S:OPS-03|Backup encryption is on, and we test restoring from backup at least every six months.⟧
- ⟦S:AUTHZ-02|Internal users get only the roles their job requires; roles are defined per service.⟧
- ⟦S:DATA-02|Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.⟧
- ⟦S:AUTHZ-04|Admin and debug endpoints are reachable only from the internal network, not from the public internet.⟧
- ⟦S:AUTHZ-05|Production access rights are reviewed at least quarterly.⟧

## data

- ⟦S:CRYPTO-02|PANs are never stored in clear and are tokenized by the card token vault.⟧
- ⟦S:AUTH-03|Tokens are short-lived (15 minutes maximum) and refresh tokens are single-use, so each refresh issues a new one.⟧
- ⟦S:CRYPTO-05|Approved algorithms only; MD5, SHA-1, DES, 3DES and ECB are prohibited.⟧
- ⟦S:DATA-03|Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.⟧

## secrets / net

- ⟦S:SECRET-01|No secrets in code, config, specs or infra definitions.⟧
- ⟦S:NET-01|DB and brokers in private subnets, not publicly reachable.⟧

## logs

- ⟦S:LOG-01|Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.⟧
- ⟦S:CRYPTO-06|Keys are managed in KMS, never stored next to the encrypted data, and rotated annually.⟧
- ⟦S:DATA-05|Each export file is encrypted at rest, readable only by the authorized requester, and removed automatically after 72 hours.⟧

## app / ops

- ⟦S:API-05|Parameterized queries only.⟧
- ⟦S:OPS-01|CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.⟧
- ⟦S:AUTHZ-01|Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.⟧

## sizing

- peak ~400 tokenize/s at month end, detokenize ~half
- 1 instance + standby DB is enough for launch (TBD, needs load test)
- RTO 4h regional

## deploy

- rolling, canary 1% for 15 min, auto rollback on error-rate threshold
- key rotation worker weekly in stg, prod schedule TBD
