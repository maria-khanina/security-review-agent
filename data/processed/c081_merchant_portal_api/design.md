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

Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS. Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it. Access rights to production systems are reviewed at least quarterly.

Personally identifiable information is encrypted at rest with AES-256. Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.

Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.

portal-db and the message brokers sit in private subnets and are not publicly reachable.

### 5. Deployment

portal-backend runs as three replicas behind the internal load balancer. Rolling updates replace one replica at a time.

---

## Part B (Mei, backend side)

#### reports and queries

The backend (portal-backend, I also say "the portal service") builds reports in a worker. A job goes requested, running, ready. Only one job per type and range runs at a time per merchant. For the filtered lists and the report queries, dynamic queries are assembled with string formatting because the ORM is too slow. We measured it on the settlement list and the difference was big.

#### logging

- Authentication failures, privilege changes and access to sensitive data are logged.

#### data

| area | rule |
|---|---|
| minimization | The portal collects and stores only the personal data needed to run merchant accounts. |
| third parties | Personal data is sent to third parties only under an approved data processing agreement, and only the fields required. |
| exports | Reports that contain personal data require authorization to download, are encrypted in storage and expire.

#### input and build

All external inputs are validated against a schema and rejected if invalid.

#### behavior

The invite call creates the user in a pending state and sends an activation email through the notification platform. A role change takes effect on the next token refresh. The settlements list is read from a table filled nightly by the finance pipeline, and the portal never writes to it. Download streams the file.

##### Differences between the halves

Part A says three replicas, Part B says two. Part A names the service portal-backend, Part B sometimes says "the portal service". Part A says the gateway checks callers with Keycloak, Part B has an old note that says the backend does it itself (the old note is outdated). To be cleaned up before review.
