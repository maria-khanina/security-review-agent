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
| Authentication | ⟦S:AUTH-01|External API calls are authenticated with OAuth2/OIDC bearer tokens issued by our identity provider.⟧ |
| Ownership | ⟦S:AUTHZ-01|Every request for a customer-owned case or document verifies that the caller owns the resource or is entitled to it.⟧ |
| Admin endpoints | ⟦S:AUTHZ-04|Nothing administrative or meant for debugging can be called from outside our network.⟧ |

## Data and crypto

| Topic | Rule |
|---|---|
| At rest | ⟦S:CRYPTO-01|The databases and object stores that hold PII use AES-256 encryption at rest.⟧ |
| Algorithms | ⟦S:CRYPTO-05|Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.⟧ |
| Retention | ⟦S:DATA-02|Personal data has a defined retention period and is deleted when it expires or on a verified request from the data subject.⟧ |
| Vendor | ⟦S:DATA-03|Third parties receive only the fields they need, and only if an approved data processing agreement covers them.⟧ |
| Transport | ⟦F3|All traffic is served over HTTPS only.⟧ |

## Storage and network

| Topic | Rule |
|---|---|
| Document bucket | ⟦F1|The bucket policy allows anonymous reads so downloads work without signed URLs.⟧ |
| Database reachability | ⟦F2|To simplify failover tests the database is reachable from outside the VPC.⟧ |

## Secrets, logging, application, ops

| Topic | Rule |
|---|---|
| Secrets in artifacts | ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ |
| Secrets at runtime | ⟦S:SECRET-02|On boot, the service pulls its credentials from the approved secret store.⟧ |
| Security logging | ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧ |
| Log content | ⟦S:LOG-02|Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids.⟧ |
| Validation | ⟦S:API-01|External inputs are accepted only if they validate against the schema.⟧ |
| Queries | ⟦S:API-05|We use parameterized queries only, with no SQL built from user input by string concatenation.⟧ |
| CORS | ⟦S:API-06|Browser-facing APIs allow only approved origins in CORS.⟧ |
| Pipeline | ⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧ |

## Open

| Item | Owner |
|---|---|
| Vendor callback retry window | TBD |
| Manual review SLA | TBD |
