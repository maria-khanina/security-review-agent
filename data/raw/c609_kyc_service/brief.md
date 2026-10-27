# Writer brief: c609_kyc_service

Author profile `compliance_voice`: Legalistic language citing standards and "in accordance with company policy" without saying what is actually done.
- structure=clean_headings, english=native_fluent, hedging=none, terminology=consistent, staleness=none
- typical gaps: concrete mechanism behind every claimed compliance
- length 1200-2200 words; typo rate 0.0; markdown breakage none; dangling references 0; TBD markers 0

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
- F1 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The register shows the name of the team but not of a person.
- F2 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Receipts by email show the full card number so that customers recognise the payment.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:ARC-02|...⟧ Documents uploaded by customers must be deleted within 30 days after the account is closed.
- ⟦S:VUL-01|...⟧ Vulnerabilities rated critical must be fixed in production within 7 days after they are published.
- ⟦S:TST-01|...⟧ Production data must not be copied to test or development environments.
- ⟦S:TST-02|...⟧ Test accounts in production must be removed within 7 days after the test ends.
- ⟦S:EXP-01|...⟧ Exported files that contain personal data must be encrypted and must be deleted from the download location after 7 days.
- ⟦S:EXP-02|...⟧ Exports of more than 1,000 customer records need the written approval of the data owner.
- ⟦S:INV-02|...⟧ The service register must list for each service the personal data that it processes and every third party that receives data from it.
- ⟦S:MON-01|...⟧ Alerts of severity high must be acknowledged within 15 minutes.
- ⟦S:WHK-01|...⟧ Callbacks to endpoints of customers must be signed and must carry a timestamp that the receiver can check against replay.

## Functional content (no security claims)
Aim for at least 1200 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c609_kyc_service/design_marked.md
