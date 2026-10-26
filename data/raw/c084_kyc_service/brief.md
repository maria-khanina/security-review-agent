# Writer brief: c084_kyc_service

Author profile `meeting_notes`: Written as decisions and open questions after a design meeting; some decisions are reversed later in the same doc.
- structure=meeting_notes, english=native_sloppy, hedging=high, terminology=aliases_drift, staleness=none
- typical gaps: final outcome of open questions
- length 700-1400 words; typo rate 0.01; markdown breakage none; dangling references 0; TBD markers 5

Service: Collects identity documents, calls a third-party verification vendor, stores results. (Meridian Pay, external exposure, data: pii)

Components:
- kyc-orchestrator (service)
- kyc-documents (S3) (object_storage)
- kyc-db (PostgreSQL) (database)
- Identity verification vendor (third_party)

Flows:
- Customer app -> kyc-orchestrator: identity details and document images
- kyc-orchestrator -> kyc-documents (S3): document images
- kyc-orchestrator -> kyc-db (PostgreSQL): case records
- kyc-orchestrator -> Identity verification vendor: verification request

Implementation (openapi) the document describes:
- POST /v1/kyc/cases: Open a verification case
- POST /v1/kyc/cases/{caseId}/documents: Upload an identity document
- GET /v1/kyc/cases/{caseId}: Get case status
- POST /v1/kyc/cases/{caseId}/submit: Submit the case to the verification vendor
- GET /v1/kyc/cases: List cases

## Planted items
- F1 [ambiguity, low] Mention kyc-orchestrator naturally, but do NOT state: Which external destinations the service may contact. Wrap the sentence(s) that mention kyc-orchestrator (the place where that information should have been) in the F1 marker.
- F2 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Services call each other with one long-lived token that every service reuses.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:DATA-02|...⟧ Personal data must have a defined retention period and be deleted when it expires or on verified request.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:CRYPTO-06|...⟧ Encryption keys must be held in KMS, never stored with the data they protect, and rotated at least annually.
- ⟦S:CRYPTO-07|...⟧ Services must validate TLS certificates and must not disable verification.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:NET-02|...⟧ Object storage buckets must block public access and be private by default.
- ⟦S:NET-05|...⟧ External APIs must sit behind a WAF with rate limiting.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:API-03|...⟧ Outbound and inbound webhook payloads must be signed and signatures verified.
- ⟦S:AUTH-06|...⟧ Login and token endpoints must throttle or lock out repeated failed attempts.
- ⟦S:AUTH-03|...⟧ Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- ⟦S:DATA-05|...⟧ Reports and exports containing personal data must require authorization, be encrypted in storage and expire.
- ⟦S:DATA-04|...⟧ Non-production environments must not contain real personal or card data.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:API-01|...⟧ All external inputs must be validated against a schema and rejected if invalid.
- ⟦S:API-04|...⟧ Error responses must not reveal stack traces, SQL or internal hostnames.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:API-02|...⟧ External APIs must enforce per-client rate limits.
- ⟦S:LOG-04|...⟧ Access to centralized logs must be limited to authorized staff.
- ⟦S:AUTHZ-03|...⟧ Each service must use its own database account with the minimum grants and no shared administrative credentials.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- ⟦S:OPS-02|...⟧ Containers must run as a non-root user with a read-only root filesystem where possible.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:OPS-03|...⟧ Backups must be encrypted and restoration must be tested at least twice a year.
- ⟦S:SECRET-03|...⟧ Service credentials must be rotated at least every 90 days and immediately after suspected exposure.
- ⟦S:DATA-01|...⟧ Services must collect and store only the personal data needed for their purpose.
- ⟦S:LOG-03|...⟧ Audit logs must be tamper-evident and retained for at least one year.
- ⟦S:CRYPTO-03|...⟧ All external traffic must use TLS 1.2 or higher.

## Functional content (no security claims)
Aim for at least 700 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.
Functional detail to describe for each endpoint:
- POST /v1/kyc/cases: request fields customer_id, full_name, date_of_birth, country; response fields id, status, risk_level, customer_id
- POST /v1/kyc/cases/{caseId}/documents: request fields document_type, content_base64; response fields document_id, received_at
- GET /v1/kyc/cases/{caseId}: request fields none; response fields id, status, risk_level, customer_id
- POST /v1/kyc/cases/{caseId}/submit: request fields consent; response fields id, status, risk_level, customer_id
- GET /v1/kyc/cases: request fields none; response fields id, status, risk_level, customer_id

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c084_kyc_service/design_marked.md
