# KYC Verification Service: Architecture and Security Control Catalogue

Author: Rina M., Security Champion, Identity Team
Review: Security Architecture
Revision: 5 (rev 4 used the name "KYC-Gateway" for kyc-orchestrator; the old name is retired but still appears in two dashboards)

## 1. Summary

The KYC Verification Service collects identity details and identity document images from customers, submits them to an external identity verification vendor, and keeps the outcome of each verification case. It is one of the most sensitive services in the platform because it holds government identity documents, so its controls are catalogued here in detail. Reviewers should read the catalogue (section 5) first and the architecture afterwards.

## 2. Architecture

The customer application calls kyc-orchestrator. kyc-orchestrator stores document images in the kyc-documents bucket (S3) and case records in kyc-db (PostgreSQL), and sends verification requests to the Identity verification vendor. The vendor returns its result through a signed callback.

There are five operations:

- POST /v1/kyc/cases opens a case (customer_id, full_name, date_of_birth, country) and returns id, status, risk_level and customer_id.
- POST /v1/kyc/cases/{caseId}/documents uploads a document (document_type, content_base64) and returns document_id and received_at.
- GET /v1/kyc/cases/{caseId} returns the case status.
- POST /v1/kyc/cases/{caseId}/submit submits the case to the vendor; the request carries the customer's consent flag.
- GET /v1/kyc/cases lists cases.

## 3. Case lifecycle

A case moves from opened to documents_received to submitted, and then to verified, rejected or manual_review. Manual review is handled by the operations team, who may ask the customer for more documents. A new submission after a rejection opens a new case. The risk level is assigned by the vendor and stored unchanged.

## 4. Customer sign-in

Customers sign in through the corporate identity provider, and the customer application presents the resulting token to the service. ⟦F1|kyc-orchestrator relies on the corporate identity provider for the sign-in of customers and does not keep any credentials of its own.⟧ Session handling in the mobile and web clients is described in the client design and is out of scope here.

⟦F2|kyc-orchestrator serves case and document requests on behalf of the signed-in customer, and it returns the case and document data that the request refers to.⟧

## 5. Control catalogue

The catalogue follows the Information Security Policy. Identifiers (K-1 and so on) match the compliance spreadsheet (link TBD; the older spreadsheet is stale).

### 5.1 Identity and access

- K-1: ⟦S:AUTH-01|No external endpoint serves anonymous traffic; callers present an OAuth2 token or a TLS client certificate.⟧
- K-2: ⟦S:AUTH-03|A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use.⟧
- K-4: ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧

### 5.2 Data protection

- K-5: ⟦S:CRYPTO-01|Encryption at rest with AES-256 covers personal data in databases and object storage, and its keys live in the corporate key management service.⟧
- K-6: ⟦S:CRYPTO-06|Key material is kept in KMS and separate from the data, and keys are rotated every year or sooner.⟧
- K-7: Personal data is never placed in URLs.
- K-8: Card numbers are never returned by the API.
- K-9: ⟦S:DATA-03|Third parties receive only the fields they need, and only if an approved data processing agreement covers them.⟧

⟦S:CRYPTO-04|Traffic between services and to data stores must be encrypted in transit.⟧
- K-10: ⟦S:DATA-04|Non-production environments contain no real personal or card data.⟧
- K-11: Customer deletion requests: ⟦F3|deletion requests are handled manually and often forgotten.⟧ A tracking dashboard is on the roadmap.

### 5.3 Cryptography and transport

- K-13: ⟦S:CRYPTO-05|Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.⟧
- K-14: ⟦S:CRYPTO-07|Services validate the certificates of the servers they call, and verification is never turned off.⟧

### 5.4 Secrets

- K-15: ⟦S:SECRET-01|Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.⟧

⟦S:LOG-04|Access to centralized logs must be limited to authorized staff.⟧
⟦S:API-02|The API enforces a limit of 300 requests per minute for each client and answers HTTP 429 when it is exceeded.⟧
- K-16: ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧

⟦S:LOG-02|Logs carry opaque identifiers only and never include secrets, card numbers or personal data.⟧

### 5.5 Network

- K-18: ⟦S:NET-01|kyc-db and the message brokers sit in private subnets and are not publicly reachable.⟧
- K-19: ⟦S:NET-02|The kyc-documents bucket blocks public access and is private by default.⟧
- K-20: ⟦S:NET-04|Third-party calls leave through an egress allowlist, not through open outbound access.⟧

### 5.6 Logging

- K-21: ⟦S:LOG-01|The audit trail includes authentication failures, privilege changes and sensitive-data access.⟧

### 5.7 Application security

- K-23: ⟦S:API-01|All external inputs are validated against a schema and rejected if invalid.⟧
- K-25: ⟦F4|Signature verification is skipped for the callbacks coming from the partner sandbox.⟧
- K-26: ⟦S:API-04|Internal details such as stack traces, SQL and hostnames never appear in an error response.⟧
- K-27: ⟦S:API-05|User input reaches the database only as query parameters, never as part of the query text.⟧

### 5.8 Operations

- K-28: ⟦S:OPS-01|CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧
- K-29: ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧

⟦S:NET-05|The external API sits behind a WAF that also applies rate limiting.⟧

## 6. Document handling details

Uploaded images are limited in size and checked for type before they are accepted. Each document is stored under a random object key that does not contain customer identifiers. The service never renders documents for the customer after upload; only the operations team can view them during manual review. Documents belonging to a rejected case remain linked to the case so that a later dispute can be handled with the original evidence.

## 7. Open items

- Status column for the catalogue: the controls above are listed without an implementation status; the spreadsheet carries the status (link TBD).
- The vendor callback retry window is unconfirmed.
- Reference to the previous KYC design (v1) is in the archived wiki space and may not open.
