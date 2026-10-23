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

When I started I mixed up a session and a token. A session is something the server remembers about you; a token is something you carry and show with each request. We use tokens. ⟦F1|The API authenticates callers with JWT bearer tokens.⟧ A JWT is a token that contains a few facts about the user and is signed so nobody can change them.

 Rotation means a new refresh token is issued every time one is used, and the old one dies.

## 5. What callers may do

Knowing who you are is not enough. A merchant must never see the settlements of another merchant. ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧

## 6. Traffic limits

If one client sends too many requests, everybody else suffers. ⟦F2|The API enforces per-client rate limits.⟧

## 7. Data and encryption

Encryption makes data unreadable without a key. ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧ ⟦S:CRYPTO-06|Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.⟧ ⟦S:CRYPTO-07|Services validate TLS certificates and never disable verification.⟧ ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧

About personal data. ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧ ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧

About how long to keep data, we have not decided anything yet. ⟦F3|No retention period is defined; old records stay in the database.⟧ This is the simplest rule and nobody has complained.

## 8. Secrets

A secret is anything that proves identity to a machine. ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧

## 9. Network

⟦S:NET-01|portal-db and the message brokers sit in private subnets and are not publicly reachable.⟧ ⟦S:NET-04|Services that call third parties have their egress restricted to an approved allowlist.⟧

## 10. Input, errors and callbacks

⟦S:API-01|All external inputs are validated against a schema and rejected if invalid.⟧ ⟦S:API-04|Error responses do not reveal stack traces, SQL or internal hostnames.⟧ ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧ ⟦S:API-03|Webhook payloads, outbound and inbound, are signed and the signatures are verified.⟧

## 11. Logs

⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧

## 12. Build and run

⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧ ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧

## 13. Report lifecycle

A report goes through three states: requested, running and ready. The merchant asks for a report with POST /v1/reports, receives a job id and polls the job until the status is ready. A ready report can be downloaded until its expires_at time. After that the job still exists but the file is gone, and the merchant must request the report again. Only one report of a given type and range runs at the same time per merchant, which keeps the database load predictable.

## 14. Open questions (TBD)

- Which roles besides owner, finance and support do merchants need?
- What is the biggest date range we allow for one report?
