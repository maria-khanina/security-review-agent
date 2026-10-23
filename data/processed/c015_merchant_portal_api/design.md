# Merchant Portal API: Architecture and Security Design

Author: Rina M., Security Champion, Merchant Experience team
Review: Security Architecture
Revision: 4 (older drafts used the name "Edge-GW" for the Portal Gateway; the name is retired)

## 1. Summary

The Merchant Portal API lets merchants see their settlements, manage the people who can access their account, and request transaction reports. It sits behind the Portal Gateway and serves the Merchant web app. This document describes the architecture, the API and the control catalogue of the service. The control catalogue is the part reviewers should read first, because merchants hand us the keys to their financial data and we take that trust seriously.

## 2. Architecture

The Merchant web app calls the Portal Gateway. The gateway validates the caller's token with Keycloak and forwards authenticated requests to portal-backend. portal-backend reads and writes settlements, merchant users and report jobs in portal-db (PostgreSQL). There is no other path to portal-db and no other service in the request path.

Roles in the portal are merchant-level: owner, finance and support. Every merchant user belongs to exactly one merchant account. Users are invited by an owner and receive their role at invitation time.

## 3. API

- GET /v1/settlements lists settlements; the list can be filtered by status. A settlement has id, period, gross, fees and net, all amounts in minor currency units.
- GET /v1/settlements/{settlementId} returns one settlement in the same shape.
- POST /v1/users invites a merchant user. The request carries email and role; the reply has id, email and role.
- PATCH /v1/users/{userId}/role changes a user's role; the request carries the new role.
- POST /v1/reports requests a report. The request carries report_type, from_date and to_date; the reply has id, status and expires_at.
- GET /v1/reports/{reportId}/download downloads a finished report. The reply shape is the report job (id, status, expires_at).

Reports are generated asynchronously. A report moves through requested, running and ready, and a ready report stays downloadable until its expires_at moment.

## 4. Control catalogue

The catalogue follows the Information Security Policy. Control identifiers (C-1 and so on) match the spreadsheet in the compliance folder (link TBD; the older spreadsheet under the previous team name is stale).

### 4.1 Identity and access

- C-1: All state-changing operations require an authenticated caller.
- C-6: Admin and debug endpoints are reachable only from the internal network, not from the public internet.

### 4.2 Data protection

- C-7: The databases and object stores that hold PII use AES-256 encryption at rest.
- C-8: Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.
- C-9: Card numbers are never returned by the API.
- C-12: Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.
- C-13: Only synthetic data is present outside production.

### 4.3 Cryptography and transport

- C-15: Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.
- C-16: Services validate the certificates of the servers they call, and verification is never turned off.

### 4.4 Secrets

- C-17: Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- C-18: On boot, the service pulls its credentials from the approved secret store.

### 4.5 Network

- C-20: portal-db and the message brokers sit in private subnets and are not publicly reachable.
- C-21: Egress of services that call third parties is restricted to an approved allowlist.

### 4.6 Logging

- C-22: The audit trail includes authentication failures, privilege changes and sensitive-data access.

### 4.7 Application security

- C-25: All external input is validated against a schema, and invalid requests are rejected.
- C-27: Webhook payloads, outbound and inbound, are signed and the signatures are verified.
- C-28: Error responses do not reveal stack traces, SQL or internal hostnames.
- C-29: We use parameterized queries only, with no SQL built from user input by string concatenation.

### 4.8 Operations

- C-30: The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.
- C-31: The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only.

## 5. Accepted risks and roadmap

Two items are on the roadmap rather than in release one. Bot and abuse protection for the portal is postponed until there is a measured problem. The team will revisit this after the first quarter of traffic. Single sign-on for merchants with their own identity providers is planned, but the design is not ready (TBD).

## 6. Reporting behavior

Report types cover settlements, fees and disputes. Large date ranges are split into chunks internally so that a single request cannot occupy a worker for long. Only one report of a given type and range may run at a time per merchant; a second request returns the running job. When a report finishes, the merchant owner and finance roles are allowed to download it; support users see the status only.

## 7. Open questions

- Should the invite flow allow roles beyond owner, finance and support? Product is undecided (TBD).
- Exact maximum date range per report: pending a load test.
- See also the retired "Portal v1 architecture" page for background (link goes to the old wiki and may not open).
