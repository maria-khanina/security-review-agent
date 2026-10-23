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
| NFR-1 | Authentication | ⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧ |
| NFR-2 | Tokens | ⟦S:AUTH-03|Access tokens expire within 15 minutes, and refresh tokens are rotated on use.⟧ |
| NFR-3 | Brute force | ⟦S:AUTH-06|The login and token endpoints throttle or lock out repeated failed attempts.⟧ |
| NFR-4 | Authorization | ⟦S:AUTHZ-01|Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.⟧ |
| NFR-6 | Admin surface | ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧ |
| NFR-7 | Encryption at rest | ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧ |
| NFR-8 | Keys | ⟦S:CRYPTO-06|Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.⟧ |
| NFR-10 | Certificates | ⟦S:CRYPTO-07|Services validate TLS certificates and never disable verification.⟧ |
| NFR-11 | Algorithms | ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧ |
| NFR-12 | Secrets | ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ |
| NFR-13 | Secret store | ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧ |
| NFR-15 | Network | ⟦S:NET-01|portal-db and the message brokers sit in private subnets and are not publicly reachable.⟧ |
| NFR-16 | Edge | ⟦S:NET-05|External APIs sit behind a WAF with rate limiting.⟧ |
| NFR-17 | Egress | ⟦S:NET-04|Services that call third parties have their egress restricted to an approved allowlist.⟧ |
| NFR-18 | Security logging | ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧ |
| NFR-23 | Third parties | ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧ |
| NFR-24 | Test data | ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧ |
| NFR-25 | Validation | ⟦S:API-01|All external inputs are validated against a schema and rejected if invalid.⟧ |
| NFR-27 | Webhooks | ⟦S:API-03|Webhook payloads, outbound and inbound, are signed and the signatures are verified.⟧ |
| NFR-28 | Errors | ⟦S:API-04|Error responses do not reveal stack traces, SQL or internal hostnames.⟧ |
| NFR-29 | Queries | ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧ |
| NFR-30 | Pipeline | ⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧ |
| NFR-31 | Containers | ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧ |

## Definition of done

- All acceptance criteria met and demonstrated in staging.
- API documentation updated from the OpenAPI file.
- Runbook entry for report generation failures (TBD, owner to be named).
