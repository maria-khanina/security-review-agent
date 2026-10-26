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

⟦S:AUTH-01|No external endpoint serves anonymous traffic; callers present an OAuth2 token or a TLS client certificate.⟧

 ⟦S:AUTHZ-04|Nothing administrative or meant for debugging can be called from outside our network.⟧
 ⟦S:AUTHZ-03|Database credentials are per service with least-privilege grants, and no shared admin account is used by the application.⟧
 ⟦S:AUTH-02|Service-to-service calls are authenticated, either with mutual TLS between the workloads or with a signed workload identity token.⟧

⟦S:CRYPTO-01|Personally identifiable information, in kyc-db and in the kyc-documents bucket, is encrypted at rest with AES-256.⟧ ⟦S:CRYPTO-05|Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.⟧

⟦S:SECRET-01|No secrets are kept in source code, config files, API specs or infrastructure definitions.⟧ ⟦S:SECRET-02|On boot, the service pulls its credentials from the approved secret store.⟧

⟦S:CRYPTO-03|Clients outside our network must connect with TLS 1.2 or higher, and older protocol versions are refused.⟧

 ⟦S:NET-02|The kyc-documents bucket blocks public access and is private by default.⟧

⟦S:LOG-01|We log failed logins, changes of privileges and reads of sensitive data.⟧ ⟦S:LOG-02|Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids.⟧

⟦S:DATA-03|Before personal data is shared with a third party, an approved DPA must be in place, and we send just the fields needed.⟧

⟦S:API-01|External inputs are accepted only if they validate against the schema.⟧ ⟦S:API-05|All queries use bound parameters instead of string concatenation.⟧ ⟦S:API-06|Cross-origin access is restricted to approved origins, and there is no wildcard.⟧

⟦S:OPS-03|Encrypted backups are checked by a restoration exercise at least twice a year.⟧

⟦S:LOG-03|Audit logs are written to tamper-evident storage with at least one year of retention.⟧

⟦S:CRYPTO-04|Traffic between services and to data stores must be encrypted in transit.⟧
⟦S:OPS-02|Containers must run as a non-root user with a read-only root filesystem where possible.⟧

⟦S:OPS-01|Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks.⟧

## 7. Vendor integration

The vendor interface has three operations: submit a case, receive the callback with the result, and fetch the evidence summary for a case in manual review. A thin adapter translates between the vendor's data model and the service's own, which keeps vendor-specific fields out of the case record. The adapter retries failed submissions with growing delays and moves a case to manual_review if the vendor remains unavailable beyond a configured window. The callback endpoint accepts only requests that carry the vendor's signature.

## 8. Document handling

Uploaded images are limited in size and type-checked before they are accepted. Each object is stored under a random key that contains no applicant identifiers. The service never shows a document back to the applicant after upload; only the operations team can view documents during manual review.

## 9. Capacity and operations

The expected volume is a few thousand cases per day, with uploads clustered in the evening. kyc-orchestrator is stateless and scales horizontally behind the gateway; kyc-db runs as a primary with a standby in a second availability zone. Deployments are rolling with a small canary for fifteen minutes. The recovery objective for a regional failure is four hours, exercised in a quarterly game day.

## 10. Open items

- Ownership of key rotation for the document bucket is being clarified (TBD).
- The list of operations roles is under review with Security (TBD).
