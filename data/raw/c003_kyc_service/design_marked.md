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

3.1 ⟦S:AUTH-01|In accordance with policy, every externally reachable API endpoint of the Service authenticates callers with OAuth2/OIDC bearer tokens issued by the corporate identity provider, or with mutual TLS.⟧

3.2 ⟦S:AUTH-03|Access tokens expire within 15 minutes, and refresh tokens are rotated on every use.⟧

3.3 ⟦S:AUTH-06|The login and token endpoints of the corporate identity provider throttle or lock out repeated failed attempts.⟧

3.4 ⟦S:AUTHZ-01|For every request touching a customer-owned case or document, the Service verifies that the authenticated caller owns the resource or is explicitly entitled to it.⟧

3.6 ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧

## 4. Data Protection

4.1 ⟦S:CRYPTO-01|Personally identifiable information held in kyc-db and in the kyc-documents bucket is encrypted at rest with AES-256.⟧

4.2 ⟦S:CRYPTO-06|Encryption keys are held in KMS, are never stored alongside the data they protect, and are rotated at least annually.⟧

4.5 ⟦S:DATA-03|Personal data is sent to the verification vendor only under an approved data processing agreement, and only the fields required for verification are sent.⟧

4.6 ⟦S:DATA-04|Non-production environments do not contain real personal data; synthetic or masked data is used instead.⟧

## 5. Cryptography and Transport

5.2 ⟦S:CRYPTO-07|The Service validates TLS certificates on every outbound connection and never disables verification.⟧

5.3 ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧

## 6. Secrets Management

6.1 ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧

6.2 ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store when the Service starts.⟧

## 7. Network and Infrastructure

7.1 ⟦S:NET-01|kyc-db is deployed in private subnets and is not publicly reachable.⟧

7.2 ⟦S:NET-02|The kyc-documents bucket blocks public access and is private by default.⟧

7.3 ⟦S:NET-04|Outbound traffic from the Service is restricted to an approved allowlist that contains the verification vendor's endpoints.⟧

## 8. Logging and Monitoring

8.1 ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧

## 9. Application Security

9.1 ⟦S:API-01|All external inputs are validated against a schema and rejected if invalid.⟧

9.3 ⟦S:API-03|Webhook payloads, both inbound vendor callbacks and any outbound notifications, carry a signature that is verified by the receiver.⟧

9.4 ⟦S:API-04|Error responses do not reveal stack traces, SQL text or internal host names.⟧

9.5 ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧

## 10. Operations

10.1 ⟦S:OPS-01|The continuous integration pipeline scans dependencies and container images, and critical vulnerabilities are fixed within 14 days.⟧

10.2 ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧

## 11. Case Handling Detail

Cases in manual_review are picked up by the operations team, who can request additional documents from the customer; the customer receives a notification and can upload further documents to the same case. A case that stays in documents_received for more than the configured waiting time is closed as abandoned. Resubmission after rejection opens a new case rather than reusing the old one, so that every decision remains attached to exactly one set of documents. The status endpoint is read-heavy and is expected to be polled by the customer application; clients are encouraged to back off between polls.

#### Outstanding items

- Waiting time before a case is closed as abandoned: value TBD with Operations.
- Wording of the consent text shown to customers: TBD with Legal.
