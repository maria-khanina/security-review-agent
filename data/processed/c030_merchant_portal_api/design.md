# Merchant Portal API: requirements and design

Epic: PORTAL-120 (Merchant self-service)
Status: Ready for development

## Overview

Merchants need to see settlements, manage their own users and download transaction reports without contacting support. This epic delivers the API behind the Merchant web app. The request path is Merchant web app, Portal Gateway, portal-backend, portal-db (PostgreSQL); the gateway validates tokens with Keycloak before forwarding.

## Stories

### PORTAL-121: View settlements

As a merchant finance user, I want to list my settlements and open one so that I can reconcile payouts.

Acceptance criteria:
- GET /v1/settlements returns the settlements of my merchant, filterable by status.
- GET /v1/settlements/{settlementId} returns one settlement.
- A settlement contains id, period, gross, fees and net.

### PORTAL-122: Invite users

As a merchant owner, I want to invite colleagues so that they can use the portal.

Acceptance criteria:
- POST /v1/users accepts email and role and returns id, email and role.
- The invited user receives an email with an activation link (handled by the notification platform).

### PORTAL-123: Change a role

As a merchant owner, I want to change the role of a colleague.

Acceptance criteria:
- PATCH /v1/users/{userId}/role accepts the new role and returns the updated user.
- Owners cannot remove the last owner of an account.

### PORTAL-124: Request and download reports

As a merchant finance user, I want to request a transaction report and download it when ready.

Acceptance criteria:
- POST /v1/reports accepts report_type, from_date and to_date and returns a job with id, status and expires_at.
- GET /v1/reports/{reportId}/download returns the finished report until it expires.
- Only one report of a given type and range runs at a time per merchant.

## Non-functional requirements

These apply to all stories above. They are listed once to avoid repeating them in every ticket (TBD: link them as acceptance criteria in each story).

| ID | Area | Requirement |
|---|---|---|
| NFR-1 | Authentication | No external endpoint serves anonymous traffic; callers present an OAuth2 token or a TLS client certificate. |
| NFR-2 | Tokens | A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use. |
| NFR-3 | Brute force | After several failed sign-ins the login endpoint slows down or locks the account. |
| NFR-4 | Authorization | Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it. |
| NFR-6 | Admin surface | Debug and administrative routes are not exposed to the internet. |
| NFR-7 | Encryption at rest | All personally identifiable information is encrypted before it lands on disk, using AES-256. |
| NFR-8 | Keys | Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year. |
| NFR-10 | Certificates | Clients check the certificate chain and host name on every TLS connection and have no insecure mode. |
| NFR-11 | Algorithms | Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not. |
| NFR-12 | Secrets | Secrets stay out of the repository: not in code, configuration, specs or infrastructure files. |
| NFR-13 | Secret store | Runtime secrets are read from the secret store when the service starts. |
| NFR-15 | Network | portal-db and the message brokers sit in private subnets and are not publicly reachable. |
| NFR-16 | Edge | Public API traffic passes through a web application firewall with rate limits. |
| NFR-17 | Egress | The service can reach only allow-listed third-party hosts, and all other outbound traffic is blocked. |
| NFR-18 | Security logging | We log failed logins, changes of privileges and reads of sensitive data. |
| NFR-23 | Third parties | Third parties receive only the fields they need, and only if an approved data processing agreement covers them. |
| NFR-24 | Test data | Test and staging environments use synthetic data, never real personal data or card data. |
| NFR-25 | Validation | Requests from outside are checked against the schema and rejected if they do not conform. |
| NFR-27 | Webhooks | Webhook payloads, outbound and inbound, are signed and the signatures are verified. |
| NFR-28 | Errors | Error responses do not expose stack traces, SQL or internal hostnames. |
| NFR-29 | Queries | We use parameterized queries only, with no SQL built from user input by string concatenation. |
| NFR-30 | Pipeline | The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days. |
| NFR-31 | Containers | The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only. |

## Definition of done

- All acceptance criteria met and demonstrated in staging.
- API documentation updated from the OpenAPI file.
- Runbook entry for report generation failures (TBD, owner to be named).
