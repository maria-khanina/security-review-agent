# Writer brief: c055_kyc_service

Author profile `sprint_rusher`: Terse bullet fragments, many TBD markers, sections left as headings with one line.
- structure=bullets_only, english=native_sloppy, hedging=low, terminology=aliases_drift, staleness=none
- typical gaps: auth between internal services, encryption at rest, data retention, error handling
- length 400-900 words; typo rate 0.01; markdown breakage light; dangling references 0; TBD markers 0

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
- F1 [ambiguity, low] Mention kyc-orchestrator naturally, but do NOT state: Which algorithms protect integrity and confidentiality. Wrap the sentence(s) that mention kyc-orchestrator (the place where that information should have been) in the F1 marker.
- F2 [ambiguity, medium] Mention kyc-orchestrator naturally, but do NOT state: How the service obtains its secrets at runtime. Wrap the sentence(s) that mention kyc-orchestrator (the place where that information should have been) in the F2 marker.
- F3 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Internal services trust each other based on being inside the cluster network.
- F4 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Any authenticated caller can read any record if it knows the identifier.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:AUTHZ-05|...⟧ Access rights to production systems must be reviewed at least quarterly.
- ⟦S:CRYPTO-03|...⟧ All external traffic must use TLS 1.2 or higher.
- ⟦S:LOG-04|...⟧ Access to centralized logs must be limited to authorized staff.
- ⟦S:AUTH-01|...⟧ Every externally reachable API endpoint must authenticate callers with OAuth2/OIDC bearer tokens or mutual TLS.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:NET-02|...⟧ Object storage buckets must block public access and be private by default.
- ⟦S:DATA-01|...⟧ Services must collect and store only the personal data needed for their purpose.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:DATA-05|...⟧ Reports and exports containing personal data must require authorization, be encrypted in storage and expire.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:API-01|...⟧ All external inputs must be validated against a schema and rejected if invalid.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:CRYPTO-04|...⟧ Traffic between services and to data stores must be encrypted in transit.
- ⟦S:NET-05|...⟧ External APIs must sit behind a WAF with rate limiting.
- ⟦S:AUTH-03|...⟧ Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- ⟦S:OPS-03|...⟧ Backups must be encrypted and restoration must be tested at least twice a year.
- ⟦S:DATA-02|...⟧ Personal data must have a defined retention period and be deleted when it expires or on verified request.
- ⟦S:LOG-03|...⟧ Audit logs must be tamper-evident and retained for at least one year.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:CRYPTO-06|...⟧ Encryption keys must be held in KMS, never stored with the data they protect, and rotated at least annually.

## Functional content (no security claims)
Aim for at least 400 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c055_kyc_service/design_marked.md
