# card token vault: infra tables

see also wiki "vault v1" (page moved, link dead)

## Components

| Component | Kind | Role |
|---|---|---|
| tokenization-service | service | tokenize / detokenize |
| vault-db (PostgreSQL) | database | encrypted card records + token mapping |
| Vault and KMS | secret store | data keys, runtime secrets |
| vault private subnet | network | boundary around the above |

## Terraform resources

| Resource | Name | Purpose |
|---|---|---|
| kms | vault_key | root key |
| rds | vault_db | card database |
| sg | vault_db_sg | database ingress |
| loggroup | vault_audit | audit trail |
| backup_vault | vault_backups | database backups |
| iam | vault_service_policy | service role permissions |

## Flows

| From | To | Data |
|---|---|---|
| Payment services | tokenization-service | PANs to tokenize, tokens to detokenize |
| tokenization-service | vault-db | encrypted card data |
| tokenization-service | Vault and KMS | data encryption key requests |

## Database

| Topic | Statement |
|---|---|
| Content | ⟦F2|vault-db (PostgreSQL) holds the encrypted card records and the token mapping.⟧ |
| Reachability | The database accepts connections only from the application subnet. |
| Service role | The service role can only read its own table. |
| Queries | ⟦S:API-05|All queries use bound parameters instead of string concatenation.⟧ |

## Access

| Topic | Statement |
|---|---|
| Internal calls | ⟦S:AUTH-02|Calls from payment services to the tokenization-service are authenticated with mutual TLS or signed workload identity tokens.⟧ |
| Tokens | ⟦S:AUTH-03|Tokens are short-lived (15 minutes maximum) and refresh tokens are single-use, so each refresh issues a new one.⟧ |
| Test data | ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧ |

⟦S:AUTHZ-01|Each request for a customer's resource checks that the caller owns it or is entitled to it.⟧
⟦S:LOG-02|Log lines are kept free of secrets, card numbers and personal details, and identifiers are opaque.⟧
⟦S:DATA-03|Before personal data is shared with a third party, an approved DPA must be in place, and we send just the fields needed.⟧
⟦S:DATA-02|Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.⟧
⟦S:AUTHZ-04|Debug and administrative routes are not exposed to the internet.⟧
⟦S:DATA-05|Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.⟧
⟦S:DATA-01|The service stores only the personal fields that appear in its data inventory with a stated purpose.⟧
⟦S:AUTHZ-03|Database credentials are per service with least-privilege grants, and no shared admin account is used by the application.⟧
⟦S:SECRET-03|Service credentials are rotated at least every 90 days and immediately if they may have been exposed.⟧
⟦S:API-01|External inputs are accepted only if they validate against the schema.⟧
⟦S:OPS-03|Backup encryption is on, and we test restoring from backup at least every six months.⟧
⟦S:LOG-04|Reading centralized logs requires authorization, and only approved staff have it.⟧
⟦S:API-04|The API returns sanitized errors with no stack traces, SQL fragments or internal hostnames.⟧

## Cryptography

| Topic | Statement |
|---|---|
| PANs | ⟦S:CRYPTO-02|Card numbers are never stored in clear text; they are replaced by tokens from the card token vault.⟧ |
| In transit | ⟦S:CRYPTO-04|Traffic between services, and between services and data stores or brokers, is encrypted in transit.⟧ |
| Keys | ⟦S:CRYPTO-06|Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year.⟧ |
| Certificates | ⟦F1|The client library is configured to ignore certificate errors after a failed deployment.⟧ |

## Secrets

| Topic | Statement |
|---|---|
| In artifacts | ⟦S:SECRET-01|Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.⟧ |
| At runtime | ⟦S:SECRET-02|At startup the service fetches its secrets from the approved secret store.⟧ |

## Network and callbacks

| Topic | Statement |
|---|---|
| Egress | ⟦S:NET-04|Third-party calls leave through an egress allowlist, not through open outbound access.⟧ |
| Callbacks | ⟦S:API-03|Every webhook we send or receive is signed with an HMAC, and the receiver checks the signature together with the timestamp.⟧ |

## Logging

| Topic | Statement |
|---|---|
| Security events | ⟦S:LOG-01|The audit trail includes authentication failures, privilege changes and sensitive-data access.⟧ |

## Backups and build

| Topic | Statement |
|---|---|
| Backups | Backups are encrypted. |
| Pipeline | ⟦F3|Container images are never rescanned after the first build.⟧ |
| Containers | ⟦S:OPS-02|No container runs as root, and the root filesystem is read-only wherever possible.⟧ |

## Sizing

| Metric | Value |
|---|---|
| Peak tokenize rate | a few hundred per second at month end |
| Detokenize rate | about half of tokenize |
| Regional recovery objective | four hours |
| Deployment | rolling, one instance at a time |
