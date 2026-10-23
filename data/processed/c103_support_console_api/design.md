# support console api - tables

## components

| component | kind | role |
|---|---|---|
| Support web console | client_app | agent UI |
| console-backend | service | implements the API |
| console-db (PostgreSQL) | database | customer copies, agent actions |
| Keycloak | identity_provider | agent tokens |

## flows

| from | to | data |
|---|---|---|
| Support web console | console-backend | lookups, account actions |
| console-backend | Keycloak | token validation |
| console-backend | console-db (PostgreSQL) | profiles, action records |

## endpoints

| method | path | request | response |
|---|---|---|---|
| GET | /v1/customers | - | id, full_name, email, phone_number, status |
| GET | /v1/customers/{customerId} | - | id, full_name, email, phone_number, status |
| POST | /v1/customers/{customerId}/second-factor-reset | reason, ticket_id | id, status |
| POST | /v1/customers/{customerId}/credits | amount, currency, reason, ticket_id | id, amount, currency, status |
| GET | /v1/agent-actions | - | id, agent_id, action, created_at |
| POST | /v1/customers/{customerId}/data-export | format, reason | id, status, expires_at |

## controls: identity and access

| area | statement |
|---|---|
| tokens | Access tokens expire within 15 minutes, and refresh tokens are rotated on use. |
| admin sign-in | Administrative and back-office access requires multi-factor authentication. |
| passwords | User passwords are stored only as salted argon2id or bcrypt hashes; reversible storage is prohibited. |
| exposure | Administrative and debug endpoints are not reachable from the public internet. |

## controls: cryptography and secrets

| area | statement |
|---|---|
| PII at rest | Personally identifiable information is encrypted at rest with AES-256. |
| algorithms | Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited. |
| keys | Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually. |
| TLS | Services validate TLS certificates and never disable verification. |
| repo and config | Secrets do not appear in source code, configuration files, specifications or infrastructure definitions. |
| runtime | Runtime secrets are fetched from the approved secret store at startup. |

## controls: network, logging, data, delivery

| area | statement |
|---|---|
| subnets | The database and the message brokers sit in private subnets and are not publicly reachable. |
| egress | Services that call third parties have their egress restricted to an approved allowlist. |
| logging | Authentication failures, privilege changes and access to sensitive data are logged. |
| sharing | Personal data is sent to third parties only under an approved data processing agreement, and only the fields required. |
| non-prod | Non-production environments do not contain real personal or card data. |
| callbacks | Callback payloads, outbound and inbound, are signed, and the signatures are verified. |
| queries | Database queries are parameterized, and concatenating user input into queries is prohibited. |
| CI | The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days. |
| containers | Containers run as a non-root user, with a read-only root filesystem where possible. |

## limits

| item | value |
|---|---|
| search results | 50 per call |
| profile refresh | hourly |
| credit per ticket | 1 |
