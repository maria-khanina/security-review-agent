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
| Internal calls | Internal service calls to ledger-core are authenticated with mutual TLS or signed workload identity tokens. |
| Tokens | Access tokens expire within 15 minutes, and refresh tokens are rotated on use. |
| Keys | Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually. |

## Transport and crypto

| Topic | Statement |
|---|---|
| Internal traffic | Traffic between services, and between services and data stores or brokers, is encrypted in transit. |
| Algorithms | Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited. |
| Certificates | Services validate TLS certificates and never disable verification. |

## Secrets and network

| Topic | Statement |
|---|---|
| In artifacts | Secrets do not appear in source code, configuration files, specifications or infrastructure definitions. |
| At runtime | Runtime secrets are fetched from the approved secret store at startup. |
| Placement | ledger-db and the Kafka brokers sit in private subnets and are not publicly reachable. |
| Egress | Services that call third parties have their egress restricted to an approved allowlist. |

## Logging, data, code, ops

| Topic | Statement |
|---|---|
| Security events | Authentication failures, privilege changes and access to sensitive data are logged. |
| Test data | Non-production environments do not contain real personal or card data. |
| Callbacks | Webhook payloads, outbound and inbound, are signed and the signatures are verified. |
| Queries | Database queries are parameterized, and concatenating user input into queries is prohibited. |
| Pipeline | The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days. |
| Containers | Containers run as a non-root user, with a read-only root filesystem where possible. |

## Reconciliation

| Item | Value |
|---|---|
| Job | nightly, after midnight UTC |
| Check | sum of entries equals sum of balances |
| On difference | page the finance engineer on call |
