# Merchant Portal API: stories and design

Epic: PORTAL-200 (Merchant portal, reporting and users)
Status: In development

## Overview

This epic delivers settlements, user management and transaction reports for merchants. The request path is Merchant web app, Portal Gateway, portal-backend and portal-db (PostgreSQL). The gateway validates tokens against Keycloak before forwarding requests to portal-backend.

## Stories

### PORTAL-201: Settlements

As a finance user, I want to list settlements and open one so that I can reconcile payouts.

Acceptance criteria:
- GET /v1/settlements returns my merchant's settlements and can be filtered by status.
- GET /v1/settlements/{settlementId} returns id, period, gross, fees and net.

### PORTAL-202: Users

As a merchant owner, I want to invite colleagues and change their roles.

Acceptance criteria:
- POST /v1/users accepts email and role and returns id, email and role.
- PATCH /v1/users/{userId}/role accepts the new role and returns the user.
- An account always keeps at least one owner.

### PORTAL-203: Reports

As a finance user, I want to request a transaction report and download it.

Acceptance criteria:
- POST /v1/reports accepts report_type, from_date and to_date and returns a job with id, status and expires_at.
- GET /v1/reports/{reportId}/download returns the finished report until it expires.

## Delivery notes

1. All traffic is served over HTTPS only.
2. Requests are validated against strict schemas.
3. Audit trail: ⟦F1|audit logs follow the default log retention of about a month and are not write-protected.⟧ Finance accepted this for the first release.

## Non-functional requirements

| Area | Requirement |
|---|---|
| Authentication | ⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧ |
| Authorization | ⟦S:AUTHZ-01|Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.⟧ |
| Admin surface | ⟦S:AUTHZ-04|Admin and debug endpoints are reachable only from the internal network, not from the public internet.⟧ |
| Access review | ⟦S:AUTHZ-05|Every three months the system owners review who has access to production and remove what is no longer needed.⟧ |
| Encryption at rest | ⟦S:CRYPTO-01|All personally identifiable information is encrypted before it lands on disk, using AES-256.⟧ |
| Algorithms | ⟦S:CRYPTO-05|The approved algorithm list is followed, and MD5, SHA-1, DES, 3DES and ECB mode are prohibited in this service.⟧ |
| Secrets in artifacts | ⟦S:SECRET-01|Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.⟧ |
| Network | ⟦S:NET-01|portal-db and the message brokers sit in private subnets and are not publicly reachable.⟧ |
| Security logging | ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧ |
| Minimization | ⟦S:DATA-01|The portal collects and stores only the personal data needed to run merchant accounts.⟧ |
| Third parties | ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧ |
| Exports | ⟦S:DATA-05|Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.⟧ |
| Queries | ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧ |

⟦S:CRYPTO-03|All public-facing endpoints terminate TLS 1.2 or higher.⟧
⟦S:API-01|Schema validation runs on every external input, and invalid data never reaches the business logic.⟧
⟦S:OPS-01|CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.⟧
⟦S:CRYPTO-04|Traffic between services, and from services to data stores, is encrypted in transit.⟧
⟦S:AUTH-03|Access tokens live for at most 15 minutes, and every refresh token is replaced when it is used.⟧
⟦S:DATA-02|Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.⟧
⟦S:LOG-04|Access to centralized logs must be limited to authorized staff.⟧
⟦S:NET-05|The external API sits behind a WAF that also applies rate limiting.⟧
⟦S:LOG-02|Log lines are kept free of secrets, card numbers and personal details, and identifiers are opaque.⟧

## Design notes

Reports are produced by a background worker that reads from a replica. A job moves through requested, running and ready, and failed jobs carry a reason and can be requested again. Large date ranges are processed in chunks that are merged when all chunks finish. The download endpoint streams the file so memory use on the service stays flat. Settlement figures come from a table filled nightly by the finance pipeline; the portal never writes to it.

## Definition of done

- All acceptance criteria demonstrated in staging.
- OpenAPI file updated and published.
- Dashboard for report queue length and failure rate exists.
