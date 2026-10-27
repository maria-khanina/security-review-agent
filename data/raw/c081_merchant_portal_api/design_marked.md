# Merchant Portal API Design

## Part A (Arjun, platform side)

### 1. Overview

The Merchant Portal API lets merchants see settlements, manage their users and request reports. It sits behind the Portal Gateway and serves the Merchant web app.

### 2. Components

- Portal Gateway: single ingress for the web app.
- Keycloak: identity provider for merchant users; the gateway uses it to check callers.
- portal-backend: settlements, users, reports.
- portal-db (PostgreSQL): settlements, merchant users and report jobs.

### 3. API

- GET /v1/settlements lists settlements, filterable by status.
- GET /v1/settlements/{settlementId} returns id, period, gross, fees and net.
- POST /v1/users invites a user (email, role) and returns id, email and role.
- PATCH /v1/users/{userId}/role changes a role.
- POST /v1/reports requests a report (report_type, from_date, to_date) and returns a job with id, status and expires_at.
- GET /v1/reports/{reportId}/download downloads a finished report.

The service exposes only the endpoints listed in the API section. All traffic is served over HTTPS only.

### 4. Security (platform view)

⟦S:AUTH-01|External API calls are authenticated with OAuth2/OIDC bearer tokens issued by our identity provider.⟧ ⟦S:AUTHZ-01|Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.⟧ ⟦S:AUTHZ-05|Production access rights are reviewed every quarter.⟧

⟦S:DATA-02|We keep personal data for 12 months at most and delete it automatically when the period ends, or earlier on a verified request.⟧
⟦S:OPS-03|Encrypted backups are checked by a restoration exercise at least twice a year.⟧

⟦S:LOG-03|Audit logs are written to tamper-evident storage with at least one year of retention.⟧

⟦S:CRYPTO-03|All external traffic must use TLS 1.2 or higher.⟧
⟦S:LOG-04|Read access to the logging platform is granted per role: on-call engineers need it to find faults, security analysts need it to follow up alerts, and no other role is given access.⟧

⟦S:CRYPTO-01|Stored PII is protected with AES-256 encryption or stronger.⟧ ⟦S:CRYPTO-05|Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.⟧

⟦F2|Internal services trust each other because of the cluster network they sit in, and internal calls carry no credentials.⟧

⟦S:SECRET-01|No secrets are kept in source code, config files, API specs or infrastructure definitions.⟧
⟦S:CRYPTO-06|Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year.⟧

⟦S:NET-01|portal-db and the message brokers sit in private subnets and are not publicly reachable.⟧

### 5. Deployment

portal-backend runs as three replicas behind the internal load balancer. Rolling updates replace one replica at a time.

---

## Part B (Mei, backend side)

#### reports and queries

The backend (portal-backend, I also say "the portal service") builds reports in a worker. A job goes requested, running, ready. Only one job per type and range runs at a time per merchant. For the filtered lists and the report queries, ⟦F1|dynamic queries are assembled with string formatting because the ORM is too slow.⟧ We measured it on the settlement list and the difference was big.

#### logging

- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧

#### data

| area | rule |
|---|---|
| minimization | ⟦S:DATA-01|A register of personal fields with the purpose of each is kept for the service, and anything that is not in the register is not stored.⟧ |
| third parties | ⟦S:DATA-03|Third-party transfers are covered by an approved data processing agreement and are limited to the listed fields, which the vendor needs to perform the service; all other fields are removed before sending.⟧ |
| exports | ⟦S:DATA-05|Each export file is encrypted at rest, readable only by the authorized requester, and removed automatically after 72 hours.⟧

#### input and build

⟦S:API-01|All external input is validated against a schema, and invalid requests are rejected.⟧

#### behavior

The invite call creates the user in a pending state and sends an activation email through the notification platform. A role change takes effect on the next token refresh. The settlements list is read from a table filled nightly by the finance pipeline, and the portal never writes to it. Download streams the file.

##### Differences between the halves

Part A says three replicas, Part B says two. Part A names the service portal-backend, Part B sometimes says "the portal service". Part A says the gateway checks callers with Keycloak, Part B has an old note that says the backend does it itself (the old note is outdated). To be cleaned up before review.
