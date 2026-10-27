# Ledger service

## Components

| Component | Kind | Role |
|---|---|---|
| ledger-core | service | posts entries, answers balances |
| ledger-db | PostgreSQL | entries, balances |
| ledger-events | Kafka | posted-entry events |

## Flows

| From | To | Data |
|---|---|---|
| Wallet and payment services | ledger-core | journal entries |
| ledger-core | ledger-db | entries, balances |
| ledger-core | ledger-events | posted-entry events |

## Endpoints

| Method | Path | Request | Response |
|---|---|---|---|
| POST | /v1/entries | debit_account, credit_account, amount, currency, reference | id, debit_account, credit_account, amount, posted_at |
| GET | /v1/entries/{entryId} | - | same as above |
| GET | /v1/accounts/{accountId}/balance | - | account_id, balance, currency |
| POST | /v1/entries/{entryId}/reversal | reason | cancelling entry |
| GET | /v1/entries | - | list of entries |

## Behavior

| Topic | Rule |
|---|---|
| Balance | sum of the account's entries, never stored |
| Currency | both sides must match, else rejected |
| Idempotency | same reference returns the original entry |
| Reversal | cancelling entry, once per entry |
| Roles | ledger-core applies the roles of its callers and of the finance users to every call. |

## Access and keys

| Topic | Statement |
|---|---|
| Internal calls | Service-to-service calls are authenticated, either with mutual TLS between the workloads or with a signed workload identity token. |
| Tokens | A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use. |
| Keys | KMS holds the keys, the data stores only keep ciphertext, and key rotation happens at least yearly. |

Nothing administrative or meant for debugging can be called from outside our network.
Backup encryption is on, and we test restoring from backup at least every six months.
Error responses do not expose stack traces, SQL or internal hostnames.
Audit logs are tamper-evident and kept for at least a year.
Read access to the logging platform is granted per role: on-call engineers need it to find faults, security analysts need it to follow up alerts, and no other role is given access.
Service credentials are rotated at least every 90 days and immediately if they may have been exposed.

## Transport and crypto

| Topic | Statement |
|---|---|
| Internal traffic | Traffic between services, and between services and data stores or brokers, is encrypted in transit. |
| Algorithms | We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode. |
| Certificates | Outbound TLS connections always verify the peer certificate. |

## Secrets and network

| Topic | Statement |
|---|---|
| In artifacts | No secrets are kept in source code, config files, API specs or infrastructure definitions. |
| At runtime | The approved secret manager is the only source of runtime secrets, fetched at start-up. |
| Placement | ledger-db and the Kafka brokers sit in private subnets and are not publicly reachable. |
| Egress | The service can reach only allow-listed third-party hosts, and all other outbound traffic is blocked. |

## Logging, data, code, ops

| Topic | Statement |
|---|---|
| Security events | The audit trail includes authentication failures, privilege changes and sensitive-data access. |
| Test data | Non-production environments do not contain real personal or card data. |
| Callbacks | Inbound and outbound webhooks include an HMAC signature and a timestamp; verification of both is mandatory on the receiving side. |
| Queries | Database queries are parameterized, and user input is never concatenated into SQL. |
| Pipeline | Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less. |
| Containers | The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only. |

## Reconciliation

| Item | Value |
|---|---|
| Job | nightly, after midnight UTC |
| Check | sum of entries equals sum of balances |
| On difference | page the finance engineer on call |
