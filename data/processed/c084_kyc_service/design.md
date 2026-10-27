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

We keep personal data for 12 months at most and delete it automatically when the period ends, or earlier on a verified request.

**Storage and crypto.** Personal data in our databases and object storage is encrypted at rest with AES-256, using keys held in the corporate key management service. Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year. Outbound TLS connections always verify the peer certificate. We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode. The kyc-documents bucket blocks public access and is private by default.

Rotation of service credentials happens every 90 days or sooner, and immediately after suspected exposure.

Each personal field we store is documented in the data inventory together with its purpose, and fields with no purpose are dropped.

A WAF with rate limiting protects the externally exposed API.
External traffic is served over TLS 1.2 or newer.

The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.

Services call each other with one long-lived token that every service reuses.

**Vendor.** kyc-orchestrator talks to the verification vendor and receives its callbacks. The vendor receives the customer id and the email only, as these are the fields its notification task needs, and a data processing agreement covers the transfer. Webhook payloads, inbound and outbound, carry an HMAC signature and a timestamp, and the receiver verifies both. Open: retry window for vendor timeouts (TBD).

Repeated failed logins are slowed down, and ten consecutive failures trigger a temporary lockout of the account.

A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use.
Reports and exports with personal data are available only to authorized users, stored encrypted, and deleted after 7 days.

**Data.** Retention value is TBD (compliance says five years after account closure, legal wants to check). Test and staging environments use synthetic data, never real personal data or card data.

**Secrets.** No secrets are kept in source code, config files, API specs or infrastructure definitions. At startup the service fetches its secrets from the approved secret store.

Audit logs must be tamper-evident and retained for at least one year.

**Logging.** Authentication failures, privilege changes and access to sensitive data are written to the logs.

**API hygiene.** All external input is validated against a schema, and invalid requests are rejected. The API returns sanitized errors with no stack traces, SQL fragments or internal hostnames. We use parameterized queries only, with no SQL built from user input by string concatenation.

The API enforces a limit of 300 requests per minute for each client and answers HTTP 429 when it is exceeded.

Read access to the logging platform is granted per role: on-call engineers need it to find faults, security analysts need it to follow up alerts, and no other role is given access.

The service connects with its own database account that has only SELECT and INSERT on the tables it uses, because it never updates or deletes rows; no administrative account is shared with other services.

**Pipeline and runtime.** Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks. Containers run as a non-root user, with a read-only root filesystem where possible.

Backup encryption is on, and we test restoring from backup at least every six months.

We scrub logs so that they contain neither secrets, card numbers nor personal data other than opaque identifiers.

## case states

opened > documents_received > submitted > verified / rejected / manual_review. Manual review is done by operations and they can ask for more documents. After a rejection a new case is opened.

## action items

- Lena: ask legal about the retention value (TBD).
- Pawel: confirm the vendor retry window (TBD).
- Sanjana: point to the platform doc for the auth flow (TBD).
- Ivo: rename the old diagram labels.
