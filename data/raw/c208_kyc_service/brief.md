# Writer brief: c208_kyc_service

Author profile `meeting_notes`: Written as decisions and open questions after a design meeting; some decisions are reversed later in the same doc.
- structure=meeting_notes, english=native_sloppy, hedging=high, terminology=aliases_drift, staleness=none
- typical gaps: final outcome of open questions
- length 700-1400 words; typo rate 0.01; markdown breakage light; dangling references 0; TBD markers 2

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
- F1 [ambiguity, medium] Mention kyc-orchestrator naturally, but do NOT state: Which security events raise an alert and how fast it reaches the on-call engineer. Wrap the sentence(s) that mention kyc-orchestrator (the place where that information should have been) in the F1 marker.
- F2 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Session tokens are cached in a file in the app directory so that the app starts faster.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:UPL-02|...⟧ Uploaded files must be scanned for malware before any other user or service can open them.
- ⟦S:TPC-01|...⟧ Every third-party SDK or library must be approved before its first use, and the list of approved components must be reviewed every six months.
- ⟦S:DR-01|...⟧ Databases must have point-in-time recovery enabled with at least seven days of retention.

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
- Save to data/raw/c208_kyc_service/design_marked.md
