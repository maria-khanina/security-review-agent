# Merchant Portal API: a design walkthrough for new joiners

Author: Tobias, Merchant Experience team (junior)
Reviewer: Hana

## 1. What does the portal do?

Merchants are the shops and businesses that accept payments through Meridian Pay. After a payment is made, a merchant wants to see how much money they will receive, which fees were taken, and which payments are included. The Merchant Portal API gives them that view. It also lets the owner of a merchant account invite colleagues, change what those colleagues are allowed to do, and download reports for their accountants.

## 2. The pieces

I draw the pieces like a small office:

- **Merchant web app** is the browser application that merchants see.
- **Portal Gateway** is the reception desk. All calls from the web app go to it first.
- **Keycloak** is the identity provider. The gateway asks it whether a token is valid.
- **portal-backend** is the service with the business logic: it knows how to build a settlement list, how to invite a user and how to start a report.
- **portal-db (PostgreSQL)** is the database with settlements, merchant users and report jobs.

A call travels from the web app to the gateway, then to Keycloak for the validation, then to portal-backend, and portal-backend talks to portal-db. Nothing else touches portal-db.

## 3. The API calls

- GET /v1/settlements lists the settlements of the merchant. You can filter by status. Each settlement has an id, a period, gross, fees and net amounts.
- GET /v1/settlements/{settlementId} returns one settlement in the same shape.
- POST /v1/users invites a user; the request has an email and a role, and the reply returns the id, email and role.
- PATCH /v1/users/{userId}/role changes the role of a user.
- POST /v1/reports asks for a report; the request has a report_type and a date range (from_date and to_date), and the reply is a job with id, status and expires_at.
- GET /v1/reports/{reportId}/download downloads the finished report.

## 4. How callers prove who they are

When I started I mixed up a session and a token. A session is something the server remembers about you; a token is something you carry and show with each request. We use tokens. The API authenticates callers with JWT bearer tokens. A JWT is a token that contains a few facts about the user and is signed so nobody can change them.

 Rotation means a new refresh token is issued every time one is used, and the old one dies.

## 5. What callers may do

Knowing who you are is not enough. A merchant must never see the settlements of another merchant. ⟦S:AUTHZ-04|The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.⟧

## 6. Traffic limits

If one client sends too many requests, everybody else suffers. The API enforces per-client rate limits.

## 7. Data and encryption

Encryption makes data unreadable without a key. ⟦S:CRYPTO-01|Personal data in our databases and object storage is encrypted at rest with AES-256, using keys held in the corporate key management service.⟧ ⟦S:CRYPTO-06|KMS holds the keys, the data stores only keep ciphertext, and key rotation happens at least yearly.⟧ ⟦S:CRYPTO-07|TLS certificate verification is enabled in all clients, with no option to disable it.⟧ ⟦S:CRYPTO-05|Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.⟧

⟦S:LOG-02|Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.⟧

About personal data. ⟦S:DATA-03|Third parties receive only the fields they need, and only if an approved data processing agreement covers them.⟧ ⟦S:DATA-04|Non-production environments contain no real personal or card data.⟧

⟦S:DATA-01|The data inventory of the service lists every stored personal field with its purpose, and a field without a listed purpose is not collected.⟧

⟦S:CRYPTO-03|All public-facing endpoints terminate TLS 1.2 or higher.⟧

⟦S:AUTH-03|Access tokens live for at most 15 minutes, and every refresh token is replaced when it is used.⟧

About how long to keep data, we have not decided anything yet. ⟦F1|No retention period is defined; old records stay in the database.⟧ This is the simplest rule and nobody has complained.

## 8. Secrets

A secret is anything that proves identity to a machine. ⟦S:SECRET-01|Source, config, specs and infrastructure definitions contain no secrets.⟧ ⟦S:SECRET-02|Runtime secrets are read from the secret store when the service starts.⟧

## 9. Network

⟦S:NET-01|portal-db and the message brokers sit in private subnets and are not publicly reachable.⟧ ⟦S:NET-04|Outbound calls to third parties are restricted to an approved allowlist.⟧

⟦S:AUTH-01|Every externally reachable API endpoint must authenticate callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧
⟦S:API-02|The API enforces a limit of 300 requests per minute for each client and answers HTTP 429 when it is exceeded.⟧

## 10. Input, errors and callbacks

⟦S:API-01|All external input is validated against a schema, and invalid requests are rejected.⟧ ⟦S:API-04|Error responses do not expose stack traces, SQL or internal hostnames.⟧ ⟦S:API-05|Database queries are parameterized, and user input is never concatenated into SQL.⟧ ⟦F2|Webhook payloads are not signed; receivers trust the callback URL they registered.⟧

⟦S:AUTHZ-01|Ownership is verified on every access to customer-owned data, not only at login.⟧
⟦S:SECRET-03|Credentials rotate on a 90-day cycle at the latest, and at once after a suspected leak.⟧

⟦S:AUTH-06|Brute-force protection: throttling of failed attempts on the login and token endpoints, plus a temporary lockout after ten failures in a row.⟧
⟦S:CRYPTO-04|Traffic between services, and from services to data stores, is encrypted in transit.⟧
⟦S:LOG-04|Access to the central logs is limited to the on-call engineers of the owning team, who need it to investigate incidents, and to the security analysts, who need it to review audit events.⟧
⟦S:AUTHZ-03|The service connects with its own database account that has only SELECT and INSERT on the tables it uses, because it never updates or deletes rows; no administrative account is shared with other services.⟧

⟦S:AUTH-02|We do not trust the internal network by itself: every internal call is authenticated with mTLS or workload identity tokens.⟧

## 11. Logs

⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧

## 12. Build and run

⟦S:OPS-01|Every build scans libraries and container images, and critical vulnerabilities get a 14-day fix deadline.⟧ ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧

⟦S:NET-05|A WAF with rate limiting protects the externally exposed API.⟧

## 13. Report lifecycle

A report goes through three states: requested, running and ready. The merchant asks for a report with POST /v1/reports, receives a job id and polls the job until the status is ready. A ready report can be downloaded until its expires_at time. After that the job still exists but the file is gone, and the merchant must request the report again. Only one report of a given type and range runs at the same time per merchant, which keeps the database load predictable.

## 14. Open questions (TBD)

- Which roles besides owner, finance and support do merchants need?
- What is the biggest date range we allow for one report?
