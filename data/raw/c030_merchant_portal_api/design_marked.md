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
| NFR-1 | Authentication | ⟦S:AUTH-01|No external endpoint serves anonymous traffic; callers present an OAuth2 token or a TLS client certificate.⟧ |
| NFR-2 | Tokens | ⟦S:AUTH-03|A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use.⟧ |
| NFR-3 | Brute force | ⟦F1|Repeated failed logins are retried without any delay, and there is no lockout.⟧ |
| NFR-4 | Authorization | ⟦S:AUTHZ-01|Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.⟧ |
| NFR-6 | Admin surface | ⟦S:AUTHZ-04|Debug and administrative routes are not exposed to the internet.⟧ |
| NFR-7 | Encryption at rest | ⟦S:CRYPTO-01|Encryption at rest with AES-256 covers personal data in databases and object storage, and its keys live in the corporate key management service.⟧ |
| NFR-8 | Keys | ⟦S:CRYPTO-06|Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year.⟧ |
| NFR-10 | Certificates | ⟦S:CRYPTO-07|Clients check the certificate chain and host name on every TLS connection and have no insecure mode.⟧ |
| NFR-11 | Algorithms | ⟦S:CRYPTO-05|Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.⟧ |
| NFR-12 | Secrets | ⟦S:SECRET-01|Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.⟧ |
| NFR-13 | Secret store | ⟦S:SECRET-02|Runtime secrets are read from the secret store when the service starts.⟧ |
| NFR-15 | Network | ⟦S:NET-01|portal-db and the message brokers sit in private subnets and are not publicly reachable.⟧ |
| NFR-16 | Edge | ⟦S:NET-05|Public API traffic passes through a web application firewall with rate limits.⟧ |
| NFR-17 | Egress | ⟦S:NET-04|The service can reach only allow-listed third-party hosts, and all other outbound traffic is blocked.⟧ |
| NFR-18 | Security logging | ⟦S:LOG-01|We log failed logins, changes of privileges and reads of sensitive data.⟧ |
| NFR-23 | Third parties | ⟦S:DATA-03|Third parties receive only the fields they need, and only if an approved data processing agreement covers them.⟧ |
| NFR-24 | Test data | ⟦S:DATA-04|Test and staging environments use synthetic data, never real personal data or card data.⟧ |
| NFR-25 | Validation | ⟦S:API-01|Requests from outside are checked against the schema and rejected if they do not conform.⟧ |
| NFR-27 | Webhooks | ⟦S:API-03|Every webhook we send or receive is signed with an HMAC, and the receiver checks the signature together with the timestamp.⟧ |
| NFR-28 | Errors | ⟦F2|When a query fails, the error body contains the SQL statement that failed.⟧ |
| NFR-29 | Queries | ⟦S:API-05|We use parameterized queries only, with no SQL built from user input by string concatenation.⟧ |
| NFR-30 | Pipeline | ⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧ |
| NFR-31 | Containers | ⟦S:OPS-02|The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only.⟧ |

⟦S:AUTHZ-03|The database account of the service has the minimum grants its functions need: reads on two tables and writes on one, and the administrative credentials are held by the database team alone.⟧
⟦S:LOG-03|Audit logs are written to tamper-evident storage with at least one year of retention.⟧
⟦S:LOG-02|Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.⟧
⟦S:DATA-01|A register of personal fields with the purpose of each is kept for the service, and anything that is not in the register is not stored.⟧
⟦S:OPS-03|Backups must be encrypted and restoration must be tested at least twice a year.⟧
⟦S:SECRET-03|Service credentials must be rotated at least every 90 days and immediately after suspected exposure.⟧
⟦S:API-02|Each client is limited to 100 requests per minute, and requests above the limit receive HTTP 429.⟧
⟦S:DATA-02|Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.⟧

## Definition of done

- All acceptance criteria met and demonstrated in staging.
- API documentation updated from the OpenAPI file.
- Runbook entry for report generation failures (TBD, owner to be named).
