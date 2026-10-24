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
| tokens | ⟦S:AUTH-03|Access tokens expire within 15 minutes, and refresh tokens are rotated on use.⟧ |
| admin sign-in | ⟦S:AUTH-04|Back-office and administrative accounts cannot log in with a password alone, because MFA is enforced.⟧ |
| passwords | ⟦S:AUTH-05|User passwords are stored only as salted argon2id or bcrypt hashes; reversible storage is prohibited.⟧ |
| exposure | ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧ |

## controls: cryptography and secrets

| area | statement |
|---|---|
| PII at rest | ⟦S:CRYPTO-01|Personal data in our databases and object storage is encrypted at rest with AES-256, using keys held in the corporate key management service.⟧ |
| algorithms | ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧ |
| keys | ⟦S:CRYPTO-06|Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.⟧ |
| TLS | ⟦S:CRYPTO-07|Clients check the certificate chain and host name on every TLS connection and have no insecure mode.⟧ |
| repo and config | ⟦S:SECRET-01|Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.⟧ |
| runtime | ⟦S:SECRET-02|Runtime secrets are read from the secret store when the service starts.⟧ |

## controls: network, logging, data, delivery

| area | statement |
|---|---|
| subnets | ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧ |
| egress | ⟦S:NET-04|Egress is limited to the approved list of third-party destinations.⟧ |
| logging | ⟦S:LOG-01|Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.⟧ |
| sharing | ⟦S:DATA-03|No personal data leaves for a third party without an approved DPA, and the payload is limited to the required fields.⟧ |
| non-prod | ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧ |
| callbacks | ⟦S:API-03|Every webhook we send or receive is signed with an HMAC, and the receiver checks the signature together with the timestamp.⟧ |
| queries | ⟦S:API-05|Database queries are parameterized, and user input is never concatenated into SQL.⟧ |
| CI | ⟦S:OPS-01|Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks.⟧ |
| containers | ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧ |

⟦S:AUTH-02|Service-to-service calls are authenticated, either with mutual TLS between the workloads or with a signed workload identity token.⟧
⟦S:DATA-02|We keep personal data for 12 months at most and delete it automatically when the period ends, or earlier on a verified request.⟧
⟦S:LOG-04|Only authorized staff can access the central logs.⟧
⟦S:DATA-05|Download links for reports with personal data work for 24 hours, and the files are encrypted in storage and deleted after 7 days.⟧
⟦S:AUTHZ-01|Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.⟧
⟦S:API-01|Schema validation runs on every external input, and invalid data never reaches the business logic.⟧
⟦S:LOG-02|Logs carry opaque identifiers only and never include secrets, card numbers or personal data.⟧
⟦F1|Validation failures return the full internal exception text to the console.⟧

## limits

| item | value |
|---|---|
| search results | 50 per call |
| profile refresh | hourly |
| credit per ticket | 1 |
