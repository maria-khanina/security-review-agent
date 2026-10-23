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
| Content | ⟦F4|vault-db (PostgreSQL) holds the encrypted card records and the token mapping.⟧ |
| Reachability | ⟦F5|The database accepts connections only from the application subnet.⟧ |
| Service role | ⟦F1|The service role can only read its own table.⟧ |
| Queries | ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧ |

## Access

| Topic | Statement |
|---|---|
| Internal calls | ⟦S:AUTH-02|Calls from payment services to the tokenization-service are authenticated with mutual TLS or signed workload identity tokens.⟧ |
| Tokens | ⟦S:AUTH-03|Access tokens expire within 15 minutes, and refresh tokens are rotated on use.⟧ |
| Test data | ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧ |

## Cryptography

| Topic | Statement |
|---|---|
| PANs | ⟦S:CRYPTO-02|Primary account numbers are never stored in clear text and are tokenized by the card token vault.⟧ |
| In transit | ⟦S:CRYPTO-04|Traffic between services, and between services and data stores or brokers, is encrypted in transit.⟧ |
| Keys | ⟦S:CRYPTO-06|Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.⟧ |
| Certificates | ⟦F2|The client library is configured to ignore certificate errors after a failed deployment.⟧ |

## Secrets

| Topic | Statement |
|---|---|
| In artifacts | ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ |
| At runtime | ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧ |

## Network and callbacks

| Topic | Statement |
|---|---|
| Egress | ⟦S:NET-04|Services that call third parties have their egress restricted to an approved allowlist.⟧ |
| Callbacks | ⟦S:API-03|Token lifecycle callbacks, outbound and inbound, are signed and the signatures are verified.⟧ |

## Logging

| Topic | Statement |
|---|---|
| Security events | ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧ |

## Backups and build

| Topic | Statement |
|---|---|
| Backups | ⟦F3|Backups are encrypted.⟧ |
| Pipeline | ⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧ |
| Containers | ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧ |

## Sizing

| Metric | Value |
|---|---|
| Peak tokenize rate | a few hundred per second at month end |
| Detokenize rate | about half of tokenize |
| Regional recovery objective | four hours |
| Deployment | rolling, one instance at a time |
