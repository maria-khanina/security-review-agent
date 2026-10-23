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

Customers sign in through the corporate identity provider, and the customer application presents the resulting token to the service. kyc-orchestrator relies on the corporate identity provider for the sign-in of customers and does not keep any credentials of its own. Session handling in the mobile and web clients is described in the client design and is out of scope here.

kyc-orchestrator serves case and document requests on behalf of the signed-in customer, and it returns the case and document data that the request refers to.

## 5. Control catalogue

The catalogue follows the Information Security Policy. Identifiers (K-1 and so on) match the compliance spreadsheet (link TBD; the older spreadsheet is stale).

### 5.1 Identity and access

- K-1: Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.
- K-2: Access tokens expire within 15 minutes, and refresh tokens are rotated on use.
- K-4: Administrative and debug endpoints are not reachable from the public internet.

### 5.2 Data protection

- K-5: Personally identifiable information, in kyc-db and in the kyc-documents bucket, is encrypted at rest with AES-256.
- K-6: Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.
- K-7: Personal data is never placed in URLs.
- K-8: Card numbers are never returned by the API.
- K-9: Personal data is sent to the verification vendor only under an approved data processing agreement, and only the fields required.
- K-10: Non-production environments do not contain real personal or card data.
- K-11: Customer deletion requests: deletion requests are handled manually and often forgotten. A tracking dashboard is on the roadmap.

### 5.3 Cryptography and transport

- K-13: Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- K-14: Services validate TLS certificates and never disable verification.

### 5.4 Secrets

- K-15: Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- K-16: Runtime secrets are fetched from the approved secret store at startup.

### 5.5 Network

- K-18: kyc-db and the message brokers sit in private subnets and are not publicly reachable.
- K-19: The kyc-documents bucket blocks public access and is private by default.
- K-20: Services that call third parties have their egress restricted to an approved allowlist.

### 5.6 Logging

- K-21: Authentication failures, privilege changes and access to sensitive data are logged.

### 5.7 Application security

- K-23: All external inputs are validated against a schema and rejected if invalid.
- K-25: Webhook payloads, including the signed vendor callbacks, are signed and the signatures are verified by the receiver.
- K-26: Error responses do not reveal stack traces, SQL or internal hostnames.
- K-27: Database queries are parameterized, and concatenating user input into queries is prohibited.

### 5.8 Operations

- K-28: The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.
- K-29: Containers run as a non-root user, with a read-only root filesystem where possible.

## 6. Document handling details

Uploaded images are limited in size and checked for type before they are accepted. Each document is stored under a random object key that does not contain customer identifiers. The service never renders documents for the customer after upload; only the operations team can view them during manual review. Documents belonging to a rejected case remain linked to the case so that a later dispute can be handled with the original evidence.

## 7. Open items

- Status column for the catalogue: the controls above are listed without an implementation status; the spreadsheet carries the status (link TBD).
- The vendor callback retry window is unconfirmed.
- Reference to the previous KYC design (v1) is in the archived wiki space and may not open.
