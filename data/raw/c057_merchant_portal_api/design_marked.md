# Merchant Portal API: stories and design

Epic: PORTAL-160 (Merchant portal reporting)
Status: Ready for development
Related: PORTAL-150 (earlier phase, link may not open)

## Overview

This epic extends the Merchant Portal with settlements, user management and reports. The request path is Merchant web app, Portal Gateway, portal-backend and portal-db (PostgreSQL). The gateway validates tokens against Keycloak before forwarding requests to portal-backend.

## Stories

### PORTAL-161: Browse settlements

As a finance user, I want to list settlements and open a single settlement so that I can reconcile payouts.

Acceptance criteria:
- GET /v1/settlements returns my merchant's settlements and can be filtered by status.
- GET /v1/settlements/{settlementId} returns id, period, gross, fees and net.
- Amounts are in minor currency units.

### PORTAL-162: Invite users and change roles

As a merchant owner, I want to invite colleagues and change their roles.

Acceptance criteria:
- POST /v1/users accepts email and role and returns id, email and role.
- PATCH /v1/users/{userId}/role accepts the new role and returns the user.
- The account always keeps at least one owner.

### PORTAL-163: Request and download reports

As a finance user, I want to request a transaction report and download it.

Acceptance criteria:
- POST /v1/reports accepts report_type, from_date and to_date and returns a job with id, status and expires_at.
- GET /v1/reports/{reportId}/download returns the finished report until it expires.
- A second request for the same type and range while a job runs returns the running job.

## Non-functional requirements

Listed once for the epic.

| ID | Area | Requirement |
|---|---|---|
| NFR-1 | Authentication | ⟦S:AUTH-01|Public endpoints reject any call that carries neither a valid OAuth2 bearer token nor a client certificate.⟧ |
| NFR-2 | Authorization | ⟦S:AUTHZ-01|Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.⟧ |
| NFR-3 | Admin surface | ⟦S:AUTHZ-04|Admin and debug endpoints are reachable only from the internal network, not from the public internet.⟧ |
| NFR-4 | Access review | ⟦S:AUTHZ-05|Every three months the system owners review who has access to production and remove what is no longer needed.⟧ |
| NFR-5 | Encryption at rest | ⟦S:CRYPTO-01|Personal data is encrypted at rest with AES-256.⟧ |
| NFR-6 | Transport | ⟦S:CRYPTO-03|External traffic is served over TLS 1.2 or newer.⟧ |
| NFR-7 | Algorithms | ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧ |
| NFR-8 | Secrets in artifacts | ⟦S:SECRET-01|Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.⟧ |
| NFR-10 | Network | ⟦S:NET-01|portal-db and the message brokers sit in private subnets and are not publicly reachable.⟧ |
| NFR-11 | Security logging | ⟦F2|Access to customer records is not recorded anywhere.⟧ |
| NFR-14 | Minimization | ⟦S:DATA-01|Each personal field we store is documented in the data inventory together with its purpose, and fields with no purpose are dropped.⟧ |
| NFR-16 | Third parties | ⟦S:DATA-03|Third parties receive only the fields they need, and only if an approved data processing agreement covers them.⟧ |
| NFR-17 | Exports | ⟦S:DATA-05|Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.⟧ |
| NFR-18 | Validation | ⟦S:API-01|External inputs are accepted only if they validate against the schema.⟧ |
| NFR-19 | Queries | ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧ |

⟦S:AUTH-02|Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.⟧
⟦S:SECRET-02|The approved secret manager is the only source of runtime secrets, fetched at start-up.⟧
⟦S:CRYPTO-04|Connections to the database and between internal services use TLS.⟧
⟦S:NET-05|External APIs must sit behind a WAF with rate limiting.⟧
⟦S:OPS-01|Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks.⟧
⟦S:DATA-02|The retention period is 24 months for customer records and 90 days for delivery logs, and expired data is removed by a scheduled deletion job.⟧
⟦S:LOG-02|We scrub logs so that they contain neither secrets, card numbers nor personal data other than opaque identifiers.⟧
⟦F1|Logs can be queried by any service account in the cluster.⟧
⟦S:OPS-03|We encrypt backups and run a restore test at least twice a year.⟧
⟦S:CRYPTO-06|Key material is kept in KMS and separate from the data, and keys are rotated every year or sooner.⟧
⟦S:LOG-03|The audit trail is tamper-evident, and we keep it for no less than twelve months.⟧
⟦S:AUTH-03|Tokens are short-lived (15 minutes maximum) and refresh tokens are single-use, so each refresh issues a new one.⟧

## Design notes

Reports are produced by a background worker that reads from a replica to keep the primary free for interactive traffic. Large date ranges are split into chunks and merged when all chunks finish. Report files are generated as CSV and stored with the job until their expiry. The download endpoint streams the file so memory use on the service stays flat. Settlement figures are read from a table that is filled nightly by the finance pipeline; the portal never writes to it.

## Definition of done

- All acceptance criteria demonstrated in staging.
- The OpenAPI file is updated and published.
- A dashboard for queue length and failure rate of the report worker exists.
