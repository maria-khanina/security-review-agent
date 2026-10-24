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

- The internal endpoints of the tokenization-service are protected only by URL paths that are not published anywhere.
- Requests from outside are checked against the schema and rejected if they do not conform.
- Internal users get only the roles their job requires; roles are defined per service.
- Admin and debug endpoints are reachable only from the internal network, not from the public internet.
- Production access rights are reviewed at least quarterly.

## data

- PANs are never stored in clear and are tokenized by the card token vault.
- Approved algorithms only; MD5, SHA-1, DES, 3DES and ECB are prohibited.
- Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.

## secrets / net

- No secrets in code, config, specs or infra definitions.
- DB and brokers in private subnets, not publicly reachable.

## logs

- Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.
- Each export file is encrypted at rest, readable only by the authorized requester, and removed automatically after 72 hours.

## app / ops

- Parameterized queries only.
- Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.

## sizing

- peak ~400 tokenize/s at month end, detokenize ~half
- 1 instance + standby DB is enough for launch (TBD, needs load test)
- RTO 4h regional

## deploy

- rolling, canary 1% for 15 min, auto rollback on error-rate threshold
- key rotation worker weekly in stg, prod schedule TBD
