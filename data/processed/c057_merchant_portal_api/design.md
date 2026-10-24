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
| NFR-1 | Authentication | Public endpoints reject any call that carries neither a valid OAuth2 bearer token nor a client certificate. |
| NFR-2 | Authorization | Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it. |
| NFR-3 | Admin surface | Admin and debug endpoints are reachable only from the internal network, not from the public internet. |
| NFR-4 | Access review | Every three months the system owners review who has access to production and remove what is no longer needed. |
| NFR-5 | Encryption at rest | Personal data is encrypted at rest with AES-256. |
| NFR-6 | Transport | External traffic is served over TLS 1.2 or newer. |
| NFR-7 | Algorithms | Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited. |
| NFR-8 | Secrets in artifacts | Credentials are never committed to code, configuration, specifications or infrastructure-as-code files. |
| NFR-10 | Network | portal-db and the message brokers sit in private subnets and are not publicly reachable. |
| NFR-11 | Security logging | Access to customer records is not recorded anywhere. |
| NFR-14 | Minimization | The portal collects and stores only the personal data needed to run merchant accounts. |
| NFR-16 | Third parties | Third parties receive only the fields they need, and only if an approved data processing agreement covers them. |
| NFR-17 | Exports | Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users. |
| NFR-18 | Validation | External inputs are accepted only if they validate against the schema. |
| NFR-19 | Queries | Database queries are parameterized, and concatenating user input into queries is prohibited. |

Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.
The approved secret manager is the only source of runtime secrets, fetched at start-up.
Logs can be queried by any service account in the cluster.

## Design notes

Reports are produced by a background worker that reads from a replica to keep the primary free for interactive traffic. Large date ranges are split into chunks and merged when all chunks finish. Report files are generated as CSV and stored with the job until their expiry. The download endpoint streams the file so memory use on the service stays flat. Settlement figures are read from a table that is filled nightly by the finance pipeline; the portal never writes to it.

## Definition of done

- All acceptance criteria demonstrated in staging.
- The OpenAPI file is updated and published.
- A dashboard for queue length and failure rate of the report worker exists.
