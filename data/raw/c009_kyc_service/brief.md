# Writer brief: c009_kyc_service

Author profile `sprint_rusher`: Terse bullet fragments, many TBD markers, sections left as headings with one line.
- structure=bullets_only, english=native_sloppy, hedging=low, terminology=aliases_drift, staleness=none
- typical gaps: auth between internal services, encryption at rest, data retention, error handling
- length 400-900 words; typo rate 0.03; markdown breakage none; dangling references 0; TBD markers 0

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
- F1 [ambiguity, high] Mention kyc-orchestrator naturally, but do NOT state: Which mechanism authenticates callers of the public endpoints. Wrap the sentence(s) that mention kyc-orchestrator (the place where that information should have been) in the F1 marker.
- F2 [ambiguity, medium] Mention kyc-documents (S3) naturally, but do NOT state: Whether and how stored PII is encrypted. Wrap the sentence(s) that mention kyc-documents (S3) (the place where that information should have been) in the F2 marker.
- F3 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Access to customer records is not recorded anywhere.
- F4 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Every field received from the client is saved, in case analytics needs it later.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:CRYPTO-03|...⟧ All external traffic must use TLS 1.2 or higher.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:AUTHZ-05|...⟧ Access rights to production systems must be reviewed at least quarterly.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:NET-02|...⟧ Object storage buckets must block public access and be private by default.
- ⟦S:API-01|...⟧ All external inputs must be validated against a schema and rejected if invalid.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:CRYPTO-04|...⟧ Traffic between services and to data stores must be encrypted in transit.
- ⟦S:DATA-02|...⟧ Personal data must have a defined retention period and be deleted when it expires or on verified request.
- ⟦S:LOG-03|...⟧ Audit logs must be tamper-evident and retained for at least one year.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.

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
- Save to data/raw/c009_kyc_service/design_marked.md
