# Writer brief: c508_kyc_service

Author profile `esl_engineer`: Competent engineer writing in a second language; missing articles, literal translations of idioms, odd word order.
- structure=clean_headings, english=esl_calques, hedging=low, terminology=consistent, staleness=none
- typical gaps: negations and obligations phrased ambiguously, e.g. "should not be only encrypted"
- length 1000-1800 words; typo rate 0.03; markdown breakage none; dangling references 0; TBD markers 0

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
- F1 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Snapshots are shared with another account without checking the region.
- F2 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The pre-production environment differs so much from production that rollback tests are not trusted.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:RES-01|...⟧ Personal data of customers in the EU must be stored and processed only in regions of the EU.
- ⟦S:PIP-01|...⟧ Credentials of the delivery pipeline must be issued for each run and be valid for at most 1 hour.
- ⟦S:PIP-02|...⟧ Build artifacts must be signed, and the signature must be verified before deployment.
- ⟦S:CAP-01|...⟧ Public endpoints must shed load with HTTP 503 instead of queueing requests when their capacity is exhausted.
- ⟦S:PRV-03|...⟧ Personal data must be used only for purposes listed in the privacy notice shown to customers at sign-up.

## Functional content (no security claims)
Aim for at least 1000 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c508_kyc_service/design_marked.md
