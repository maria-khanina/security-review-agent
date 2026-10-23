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

- Payment services authenticate to the tokenization-service with mTLS or signed workload identity tokens.
- Internal users get only the roles their job requires; roles are defined per service.
- Production access rights are reviewed at least quarterly.

## data

- PANs are never stored in clear and are tokenized by the card token vault.
- Approved algorithms only; MD5, SHA-1, DES, 3DES and ECB are prohibited.

## secrets / net

- No secrets in code, config, specs or infra definitions.
- DB and brokers in private subnets, not publicly reachable.

## logs

- Auth failures, privilege changes and access to sensitive data are logged.

## app / ops

- Parameterized queries only.

## sizing

- peak ~400 tokenize/s at month end, detokenize ~half
- 1 instance + standby DB is enough for launch (TBD, needs load test)
- RTO 4h regional

## deploy

- rolling, canary 1% for 15 min, auto rollback on error-rate threshold
- key rotation worker weekly in stg, prod schedule TBD
