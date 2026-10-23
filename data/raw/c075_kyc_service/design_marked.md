# KYC Verification Service: Architecture and Design Rationale

Author: Elena R., Principal Architect, Identity and Onboarding
Status: Approved by Architecture Board

## 1. Context and goals

The KYC Verification Service turns a stranger into a verified customer. It collects identity details and identity document images from applicants, submits them to an external identity verification vendor, and keeps the outcome of each case. It holds some of the most sensitive data in the estate, which makes it a natural target and a natural audit subject.

The goals, in order of priority, are: protect the identity documents, keep every decision traceable to its evidence, keep the applicant journey short, and keep the integration with the vendor replaceable. The last goal drives several choices below: the vendor sits behind a narrow interface so that a second vendor can be added without touching the rest of the service.

## 2. Architecture overview

The applicant's application calls kyc-orchestrator. kyc-orchestrator stores document images in the kyc-documents bucket (S3), keeps case records in kyc-db (PostgreSQL) and submits cases to the Identity verification vendor. The vendor reports results through a signed callback.

⟦F1|kyc-orchestrator is the only component that applicants and operations tooling talk to, and it hides the vendor and the storage behind one consistent interface.⟧

⟦F2|kyc-documents (S3) is the bucket that holds the uploaded document images, one object per document, under a random object key.⟧

## 3. API

- POST /v1/kyc/cases opens a case from customer_id, full_name, date_of_birth and country and returns id, status, risk_level and customer_id.
- POST /v1/kyc/cases/{caseId}/documents uploads a document (document_type and content_base64) and returns a document_id and the time received.
- GET /v1/kyc/cases/{caseId} returns the status of one case.
- POST /v1/kyc/cases/{caseId}/submit submits the case to the vendor once the applicant has given consent.
- GET /v1/kyc/cases lists cases for the operations team.

## 4. Case lifecycle

A case starts as opened, moves to documents_received when the first document arrives, to submitted when the applicant consents and the case is sent, and ends as verified, rejected or manual_review. Manual review is handled by operations, who may request further documents. After a rejection the applicant may start again; a new case is opened so that each decision stays attached to exactly the evidence it was based on. The risk level is assigned by the vendor and copied unchanged into the case.

## 5. Access to cases

⟦F3|kyc-orchestrator serves case and document requests for the signed-in applicant and returns the case or document the request refers to.⟧ Operations staff use a separate set of calls with their own roles.

## 6. Controls

The controls below follow the Information Security Policy.

⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧

 ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧

⟦S:CRYPTO-01|Personally identifiable information, in kyc-db and in the kyc-documents bucket, is encrypted at rest with AES-256.⟧ ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧

⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧

 ⟦S:NET-02|The kyc-documents bucket blocks public access and is private by default.⟧

⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧ ⟦S:LOG-02|Logs contain no secrets, card numbers or personal data beyond opaque identifiers.⟧

⟦S:DATA-03|Personal data is sent to the verification vendor only under an approved data processing agreement, and only the fields required.⟧

⟦S:API-01|All external inputs are validated against a schema and rejected if invalid.⟧ ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧ ⟦S:API-06|Browser-facing APIs allow only approved origins in CORS.⟧

⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧

## 7. Vendor integration

The vendor interface has three operations: submit a case, receive the callback with the result, and fetch the evidence summary for a case in manual review. A thin adapter translates between the vendor's data model and the service's own, which keeps vendor-specific fields out of the case record. The adapter retries failed submissions with growing delays and moves a case to manual_review if the vendor remains unavailable beyond a configured window. The callback endpoint accepts only requests that carry the vendor's signature.

## 8. Document handling

Uploaded images are limited in size and type-checked before they are accepted. Each object is stored under a random key that contains no applicant identifiers. The service never shows a document back to the applicant after upload; only the operations team can view documents during manual review.

## 9. Capacity and operations

The expected volume is a few thousand cases per day, with uploads clustered in the evening. kyc-orchestrator is stateless and scales horizontally behind the gateway; kyc-db runs as a primary with a standby in a second availability zone. Deployments are rolling with a small canary for fifteen minutes. The recovery objective for a regional failure is four hours, exercised in a quarterly game day.

## 10. Open items

- Ownership of key rotation for the document bucket is being clarified (TBD).
- The list of operations roles is under review with Security (TBD).
