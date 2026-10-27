# KYC service

## Components

| Component | Kind | Holds / does |
|---|---|---|
| kyc-orchestrator | service | opens cases, takes uploads, calls vendor |
| kyc-documents | S3 bucket | identity document images |
| kyc-db | PostgreSQL | case records |
| Identity verification vendor | third party | verifies documents |

## Flows

| From | To | Data |
|---|---|---|
| Customer app | kyc-orchestrator | identity details, document images |
| kyc-orchestrator | kyc-documents | document images |
| kyc-orchestrator | kyc-db | case records |
| kyc-orchestrator | vendor | verification request |

## Endpoints

| Method | Path | Request fields | Response fields |
|---|---|---|---|
| POST | /v1/kyc/cases | customer_id, full_name, date_of_birth, country | id, status, risk_level, customer_id |
| POST | /v1/kyc/cases/{caseId}/documents | document_type, content_base64 | document_id, received_at |
| GET | /v1/kyc/cases/{caseId} | - | id, status, risk_level, customer_id |
| POST | /v1/kyc/cases/{caseId}/submit | consent | id, status, risk_level, customer_id |
| GET | /v1/kyc/cases | - | list of the above |

## States

| State | Next |
|---|---|
| opened | documents_received |
| documents_received | submitted |
| submitted | verified, rejected, manual_review |
| manual_review | verified, rejected |

## Access

| Topic | Rule |
|---|---|
| Authentication | External API calls are authenticated with OAuth2/OIDC bearer tokens issued by our identity provider. |
| Ownership | Every request for a customer-owned case or document verifies that the caller owns the resource or is entitled to it. |
| Admin endpoints | Nothing administrative or meant for debugging can be called from outside our network. |

## Data and crypto

| Topic | Rule |
|---|---|
| At rest | The databases and object stores that hold PII use AES-256 encryption at rest. |
| Algorithms | Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned. |
| Retention | Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends. |
| Vendor | Third parties receive only the fields they need, and only if an approved data processing agreement covers them. |
| Transport | All traffic is served over HTTPS only. |

Calls between our own services carry a signed workload identity token or use mutual TLS, and the receiving service checks it.
Backups must be encrypted and restoration must be tested at least twice a year.
Each service has a dedicated database account; this one is granted read access to the orders table and write access to its audit table only, since those are the only tables its functions touch.
Access tokens live for at most 15 minutes, and every refresh token is replaced when it is used.
No container runs as root, and the root filesystem is read-only wherever possible.
Audit logs must be tamper-evident and retained for at least one year.
Requests from the internet reach the API only through the WAF, where rate limits are enforced.
Rate limit per client: 60 requests per minute, with HTTP 429 and a Retry-After header once the limit is hit.

## Storage and network

| Topic | Rule |
|---|---|
| Document bucket | The bucket policy allows anonymous reads so downloads work without signed URLs. |
| Database reachability | To simplify failover tests the database is reachable from outside the VPC. |

## Secrets, logging, application, ops

| Topic | Rule |
|---|---|
| Secrets in artifacts | Secrets do not appear in source code, configuration files, specifications or infrastructure definitions. |
| Secrets at runtime | On boot, the service pulls its credentials from the approved secret store. |
| Security logging | Authentication failures, privilege changes and access to sensitive data are logged. |
| Log content | Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids. |
| Validation | External inputs are accepted only if they validate against the schema. |
| Queries | We use parameterized queries only, with no SQL built from user input by string concatenation. |
| CORS | Browser-facing APIs allow only approved origins in CORS. |
| Pipeline | The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days. |

## Open

| Item | Owner |
|---|---|
| Vendor callback retry window | TBD |
| Manual review SLA | TBD |
