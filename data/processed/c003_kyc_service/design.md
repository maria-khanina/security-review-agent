# KYC Verification Service: Design and Compliance Statement

Document owner: Compliance Engineering
Version: 1.3 (reviewed by Security Architecture)

## 1. Purpose and Scope

This document describes the design of the KYC Verification Service ("the Service") and records, for each applicable requirement of the Meridian Pay Information Security Policy, the control by which the Service satisfies that requirement. It applies to the production environment and to the environments that support it. The Service collects identity information and document images from customers, submits them to an external identity verification vendor, and stores the outcome of each verification case.

## 2. Functional Description

The Service is implemented by kyc-orchestrator, which exposes five operations to the customer application:

- POST /v1/kyc/cases opens a case. Fields: customer_id, full_name, date_of_birth, country. The reply carries id, status, risk_level and customer_id.
- POST /v1/kyc/cases/{caseId}/documents uploads an identity document. Fields: document_type and content_base64. The reply carries document_id and received_at.
- GET /v1/kyc/cases/{caseId} returns the status of one case.
- POST /v1/kyc/cases/{caseId}/submit sends the case to the vendor; the only field is the customer's consent flag.
- GET /v1/kyc/cases lists cases.

Document images are written to the kyc-documents bucket (S3). Case records are written to kyc-db (PostgreSQL). Verification requests are sent to the Identity verification vendor, and the vendor reports its result through a signed callback. A case moves through the states opened, documents_received, submitted, verified, rejected and manual_review. Risk level is assigned by the vendor and copied unchanged into the case record.

## 3. Identity and Access Control

3.1 In accordance with policy, every externally reachable API endpoint of the Service authenticates callers with OAuth2/OIDC bearer tokens issued by the corporate identity provider, or with mutual TLS.

3.2 Access tokens expire within 15 minutes, and refresh tokens are rotated on every use.

3.3 Failed attempts on the login and token endpoints are throttled, and the account is temporarily locked after ten consecutive failures.

3.4 For every request touching a customer-owned case or document, the Service verifies that the authenticated caller owns the resource or is explicitly entitled to it.

3.6 Debug and administrative routes are not exposed to the internet.

## 4. Data Protection

4.1 At rest, personal data is protected with AES-256 in both the database and object storage, with keys from the corporate key management service.

4.2 Keys are managed in KMS, never stored next to the encrypted data, and rotated annually.

4.5 The new verification vendor already receives applicant details while the data processing agreement is still being negotiated with their legal team.

4.6 Non-production environments do not contain real personal data; synthetic or masked data is used instead.

External APIs must sit behind a WAF with rate limiting.

## 5. Cryptography and Transport

5.2 The Service validates TLS certificates on every outbound connection and never disables verification.

In-transit encryption covers calls between services as well as connections to databases and queues.
Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.

5.3 Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.

## 6. Secrets Management

6.1 Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.

6.2 Runtime secrets are fetched from the approved secret store when the Service starts.

## 7. Network and Infrastructure

7.1 kyc-db is deployed in private subnets and is not publicly reachable.

7.2 The kyc-documents bucket blocks public access and is private by default.

7.3 Outbound traffic from the Service is restricted to an approved allowlist that contains the verification vendor's endpoints.

Each export file is encrypted at rest, readable only by the authorized requester, and removed automatically after 72 hours.

## 8. Logging and Monitoring

8.1 Authentication failures, privilege changes and access to sensitive data are written to the logs.

## 9. Application Security

9.1 All external inputs are validated against a schema and rejected if invalid.

9.3 Every webhook we send or receive is signed with an HMAC, and the receiver checks the signature together with the timestamp.

9.4 The API returns sanitized errors with no stack traces, SQL fragments or internal hostnames.

9.5 Database queries are parameterized, and user input is never concatenated into SQL.

The API enforces a limit of 300 requests per minute for each client and answers HTTP 429 when it is exceeded.

The application never uses a shared administrative database login; it has a dedicated, minimally privileged account.

## 10. Operations

10.1 The continuous integration pipeline scans dependencies and container images, and critical vulnerabilities are fixed within 14 days.

10.2 Workloads are non-root, and read-only root filesystems are used wherever they can be.

Calls between our own services carry a signed workload identity token or use mutual TLS, and the receiving service checks it.

## 11. Case Handling Detail

Cases in manual_review are picked up by the operations team, who can request additional documents from the customer; the customer receives a notification and can upload further documents to the same case. A case that stays in documents_received for more than the configured waiting time is closed as abandoned. Resubmission after rejection opens a new case rather than reusing the old one, so that every decision remains attached to exactly one set of documents. The status endpoint is read-heavy and is expected to be polled by the customer application; clients are encouraged to back off between polls.

#### Outstanding items

- Waiting time before a case is closed as abandoned: value TBD with Operations.
- Wording of the consent text shown to customers: TBD with Legal.
