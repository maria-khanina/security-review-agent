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
- Traffic between services and to data stores must be encrypted in transit.
- Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids.
- Requests from outside are checked against the schema and rejected if they do not conform.
- Backup encryption is on, and we test restoring from backup at least every six months.
- Internal users hold one of the service roles reader, operator or administrator, assigned by job: the support team needs reader, the platform team needs operator, and only two security leads need administrator.
- Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.
- Admin and debug endpoints are reachable only from the internal network, not from the public internet.
- Production access rights are reviewed at least quarterly.

## data

- PANs are never stored in clear and are tokenized by the card token vault.
- Tokens are short-lived (15 minutes maximum) and refresh tokens are single-use, so each refresh issues a new one.
- Approved algorithms only; MD5, SHA-1, DES, 3DES and ECB are prohibited.
- Data goes to the processor under the signed data processing agreement and only the fields it needs for the contracted task are sent: the order reference and the delivery address, because nothing else is required for delivery.

## secrets / net

- No secrets in code, config, specs or infra definitions.
- DB and brokers in private subnets, not publicly reachable.

## logs

- Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.
- Keys are managed in KMS, never stored next to the encrypted data, and rotated annually.
- Each export file is encrypted at rest, readable only by the authorized requester, and removed automatically after 72 hours.

## app / ops

- Parameterized queries only.
- CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.

## sizing

- peak ~400 tokenize/s at month end, detokenize ~half
- 1 instance + standby DB is enough for launch (TBD, needs load test)
- RTO 4h regional

## deploy

- rolling, canary 1% for 15 min, auto rollback on error-rate threshold
- key rotation worker weekly in stg, prod schedule TBD
