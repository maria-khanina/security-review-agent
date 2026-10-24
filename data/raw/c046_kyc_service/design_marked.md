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

- ⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧ ⟦S:AUTH-03|Access tokens live for at most 15 minutes, and every refresh token is replaced when it is used.⟧ ⟦S:AUTH-06|The login and token endpoints throttle repeated failures and apply a temporary lockout once an account reaches ten consecutive failed attempts.⟧

⟦S:API-02|Rate limit per client: 60 requests per minute, with HTTP 429 and a Retry-After header once the limit is hit.⟧

⟦S:DATA-02|Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.⟧
- ⟦S:AUTHZ-01|Every request for a customer-owned case or document verifies that the caller owns the resource or is entitled to it.⟧ ⟦S:AUTHZ-04|The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.⟧
- ⟦S:CRYPTO-01|Encryption at rest with AES-256 covers personal data in databases and object storage, and its keys live in the corporate key management service.⟧ ⟦S:CRYPTO-06|Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year.⟧ ⟦S:CRYPTO-07|TLS certificate verification is enabled in all clients, with no option to disable it.⟧ ⟦S:CRYPTO-05|We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.⟧

⟦S:DATA-05|Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.⟧

⟦S:NET-05|The external API sits behind a WAF that also applies rate limiting.⟧

⟦S:CRYPTO-04|Nothing travels unencrypted inside our network, because service-to-service and service-to-datastore links are encrypted.⟧
- ⟦S:SECRET-01|Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.⟧ ⟦S:SECRET-02|At startup the service fetches its secrets from the approved secret store.⟧

⟦S:AUTHZ-03|Database credentials are per service with least-privilege grants, and no shared admin account is used by the application.⟧
- ⟦S:NET-01|kyc-db and the message brokers sit in private subnets and are not publicly reachable.⟧ ⟦S:NET-02|The kyc-documents bucket blocks public access and is private by default.⟧ ⟦S:NET-04|Services that call third parties have their egress restricted to an approved allowlist.⟧
- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are written to the logs.⟧
- ⟦S:DATA-03|Third parties receive only the fields they need, and only if an approved data processing agreement covers them.⟧ ⟦S:DATA-04|Non-production environments contain no real personal or card data.⟧
- ⟦S:API-01|All external input is validated against a schema, and invalid requests are rejected.⟧ ⟦S:API-03|Webhook payloads, inbound and outbound, carry an HMAC signature and a timestamp, and the receiver verifies both.⟧ ⟦S:API-04|Clients get generic error messages without stack traces, SQL or internal hostnames.⟧ ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧
- ⟦S:OPS-01|Every build scans libraries and container images, and critical vulnerabilities get a 14-day fix deadline.⟧ ⟦S:OPS-02|The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only.⟧

## 7. Rollout

Rollout starts with new customers in one market, behind a flag, with operations watching every manual-review case. After two weeks of clean metrics, the flag opens to all customers in that market. A second market follows once the verification partner confirms its coverage of that market's documents. At each step the team reviews conversion, the manual-review rate and the partner's response times before moving on.

## 8. Open questions

- Which document types ship in the first market? Compliance and the partner are aligning (see the note in the shared drive, link may have moved).
- What wording should the consent screen use? Legal is drafting it.
