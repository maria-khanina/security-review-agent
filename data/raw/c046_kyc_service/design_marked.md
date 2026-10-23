# KYC Verification: Product and Design Overview

Owner: Onboarding Product
Status: Approved for build

## 1. Vision

Opening an account should feel like a handshake, not a form. Today, verifying a new customer takes days of back and forth, and a large share of applicants give up before they finish. The KYC Verification Service turns identity checks into a smooth, enterprise-grade, secure-by-design journey: the customer provides their details and a photo of an identity document, we check them with a trusted verification partner, and in most cases the customer is verified within minutes.

Success for the first release means three things: more applicants finish the journey, fewer cases need a human, and every decision can be explained to a regulator in plain language.

## 2. Customer value

- Applicants get a short, clear journey with fast feedback.
- Operations focus on the genuinely difficult cases instead of routine ones.
- Compliance gets a consistent record of each decision and the evidence behind it.
- Growth gets a conversion funnel it can measure and improve.

## 3. Scope

In scope: opening a verification case, uploading identity documents, submitting the case to the verification partner, tracking status and listing cases for operations. Out of scope for now: liveness checks, business (KYB) verification and re-verification campaigns.

## 4. How it works

The customer application talks to kyc-orchestrator. kyc-orchestrator keeps document images in the kyc-documents bucket (S3), keeps case records in kyc-db (PostgreSQL) and hands cases to the Identity verification vendor. The vendor reports the result back, and the service updates the case.

The API has five operations. POST /v1/kyc/cases opens a case from the customer's customer_id, full_name, date_of_birth and country, and returns the case with its id, status, risk_level and customer_id. POST /v1/kyc/cases/{caseId}/documents uploads a document (document_type and content_base64) and returns a receipt with a document_id and the time received. GET /v1/kyc/cases/{caseId} returns the status of one case. POST /v1/kyc/cases/{caseId}/submit sends the case to the partner once the customer has given consent. GET /v1/kyc/cases lists cases for the operations team.

## 5. The customer journey

A case moves through opened, documents received, submitted, and then verified, rejected or manual review. In manual review an operator may ask the customer for another document; the customer sees a friendly message and can upload more. After a rejection, the customer can start again, which opens a new case so that each decision stays attached to the evidence it was based on. The risk level assigned by the partner is shown to operations only.

## 6. Security and compliance posture

Security is a first-class feature of this service, not an afterthought, because customers trust us with their identity. The commitments below are the ones we make to customers and to the compliance team.

- ⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧ ⟦S:AUTH-03|Access tokens expire within 15 minutes, and refresh tokens are rotated on use.⟧ ⟦S:AUTH-06|The login and token endpoints throttle or lock out repeated failed attempts.⟧
- ⟦S:AUTHZ-01|Every request for a customer-owned case or document verifies that the caller owns the resource or is entitled to it.⟧ ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧
- ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧ ⟦S:CRYPTO-06|Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.⟧ ⟦S:CRYPTO-07|Services validate TLS certificates and never disable verification.⟧ ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
- ⟦S:SECRET-01|Secrets are never stored in source code, configuration files, specifications or infrastructure definitions.⟧ ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧
- ⟦S:NET-01|kyc-db and the message brokers sit in private subnets and are not publicly reachable.⟧ ⟦S:NET-02|The kyc-documents bucket blocks public access and is private by default.⟧ ⟦S:NET-04|Services that call third parties have their egress restricted to an approved allowlist.⟧
- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧
- ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧ ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧
- ⟦S:API-01|All external inputs are validated against a schema and rejected if invalid.⟧ ⟦S:API-03|Webhook payloads, including the verification partner's callbacks, are signed and the signatures are verified.⟧ ⟦S:API-04|Error responses do not reveal stack traces, SQL or internal hostnames.⟧ ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧
- ⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧ ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧

## 7. Rollout

Rollout starts with new customers in one market, behind a flag, with operations watching every manual-review case. After two weeks of clean metrics, the flag opens to all customers in that market. A second market follows once the verification partner confirms its coverage of that market's documents. At each step the team reviews conversion, the manual-review rate and the partner's response times before moving on.

## 8. Open questions

- Which document types ship in the first market? Compliance and the partner are aligning (see the note in the shared drive, link may have moved).
- What wording should the consent screen use? Legal is drafting it.
