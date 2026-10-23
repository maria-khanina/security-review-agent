# kyc service design review (notes)

Attendees: Lena, Pawel, Ivo, Sanjana
Notes: Ivo

## overview

KYC service collects identity details and document images from applicants, sends them to the external verification vendor, keeps the outcome. Pieces: kyc-orchestrator (the orchestrator, "kyc-gw" on the old slides, we should drop that), kyc-documents (S3 bucket for images), kyc-db (PostgreSQL for case records) and the Identity verification vendor.

## API

- POST /v1/kyc/cases (customer_id, full_name, date_of_birth, country) -> id, status, risk_level, customer_id
- POST /v1/kyc/cases/{caseId}/documents (document_type, content_base64) -> document_id, received_at
- GET /v1/kyc/cases/{caseId} -> status
- POST /v1/kyc/cases/{caseId}/submit (consent) -> case
- GET /v1/kyc/cases -> list

The service exposes only the endpoints listed in the API section. Pawel asked about the old health endpoint, it is gone, platform does health checks differently now.

## discussion

**Who may call.** All state-changing operations require an authenticated caller. Lena wants the exact flow in the doc, Sanjana says it is in the platform doc (TBD which one).

**Tokens and login.**

**Database.** kyc-db and the message brokers sit in private subnets and are not publicly reachable.

**Storage and crypto.** The databases and object stores that hold PII use AES-256 encryption at rest. Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year. Outbound TLS connections always verify the peer certificate. We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode. The kyc-documents bucket blocks public access and is private by default.

**Vendor.** kyc-orchestrator talks to the verification vendor and receives its callbacks. No personal data leaves for a third party without an approved DPA, and the payload is limited to the required fields. Callback payloads from the vendor are signed and the signatures are verified. Open: retry window for vendor timeouts (TBD).

**Data.** Retention value is TBD (compliance says five years after account closure, legal wants to check). Test and staging environments use synthetic data, never real personal data or card data.

**Secrets.** No secrets are kept in source code, config files, API specs or infrastructure definitions. At startup the service fetches its secrets from the approved secret store.

**Logging.** Authentication failures, privilege changes and access to sensitive data are written to the logs.

**API hygiene.** All external input is validated against a schema, and invalid requests are rejected. The API returns sanitized errors with no stack traces, SQL fragments or internal hostnames. We use parameterized queries only, with no SQL built from user input by string concatenation.

**Pipeline and runtime.** Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks. Containers run as a non-root user, with a read-only root filesystem where possible.

## case states

opened > documents_received > submitted > verified / rejected / manual_review. Manual review is done by operations and they can ask for more documents. After a rejection a new case is opened.

## action items

- Lena: ask legal about the retention value (TBD).
- Pawel: confirm the vendor retry window (TBD).
- Sanjana: point to the platform doc for the auth flow (TBD).
- Ivo: rename the old diagram labels.
