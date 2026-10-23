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
| NFR-1 | Authentication | ⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧ |
| NFR-2 | Authorization | ⟦S:AUTHZ-01|Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.⟧ |
| NFR-3 | Admin surface | ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧ |
| NFR-4 | Access review | ⟦S:AUTHZ-05|Access rights to production systems are reviewed at least quarterly.⟧ |
| NFR-5 | Encryption at rest | ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧ |
| NFR-6 | Transport | ⟦S:CRYPTO-03|All external traffic uses TLS 1.2 or higher.⟧ |
| NFR-7 | Algorithms | ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧ |
| NFR-8 | Secrets in artifacts | ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ |
| NFR-10 | Network | ⟦S:NET-01|portal-db and the message brokers sit in private subnets and are not publicly reachable.⟧ |
| NFR-11 | Security logging | ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧ |
| NFR-14 | Minimization | ⟦S:DATA-01|The portal collects and stores only the personal data needed to run merchant accounts.⟧ |
| NFR-16 | Third parties | ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧ |
| NFR-17 | Exports | ⟦S:DATA-05|Reports that contain personal data require authorization to download, are encrypted in storage and expire.⟧ |
| NFR-18 | Validation | ⟦S:API-01|All external inputs are validated against a schema and rejected if invalid.⟧ |
| NFR-19 | Queries | ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧ |

## Design notes

Reports are produced by a background worker that reads from a replica to keep the primary free for interactive traffic. Large date ranges are split into chunks and merged when all chunks finish. Report files are generated as CSV and stored with the job until their expiry. The download endpoint streams the file so memory use on the service stays flat. Settlement figures are read from a table that is filled nightly by the finance pipeline; the portal never writes to it.

## Definition of done

- All acceptance criteria demonstrated in staging.
- The OpenAPI file is updated and published.
- A dashboard for queue length and failure rate of the report worker exists.
