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

**Storage and crypto.** Personally identifiable information is encrypted at rest with AES-256. Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually. Services validate TLS certificates and never disable verification. Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited. The kyc-documents bucket blocks public access and is private by default.

**Vendor.** kyc-orchestrator talks to the verification vendor and receives its callbacks. Personal data is sent to the vendor only under an approved data processing agreement, and only the fields required. Callback payloads from the vendor are signed and the signatures are verified. Open: retry window for vendor timeouts (TBD).

**Data.** Retention value is TBD (compliance says five years after account closure, legal wants to check). Non-production environments do not contain real personal or card data.

**Secrets.** Secrets do not appear in source code, configuration files, specifications or infrastructure definitions. Runtime secrets are fetched from the approved secret store at startup.

**Logging.** Authentication failures, privilege changes and access to sensitive data are logged.

**API hygiene.** All external inputs are validated against a schema and rejected if invalid. Error responses do not reveal stack traces, SQL or internal hostnames. Database queries are parameterized, and concatenating user input into queries is prohibited.

**Pipeline and runtime.** The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days. Containers run as a non-root user, with a read-only root filesystem where possible.

## case states

opened > documents_received > submitted > verified / rejected / manual_review. Manual review is done by operations and they can ask for more documents. After a rejection a new case is opened.

## action items

- Lena: ask legal about the retention value (TBD).
- Pawel: confirm the vendor retry window (TBD).
- Sanjana: point to the platform doc for the auth flow (TBD).
- Ivo: rename the old diagram labels.
