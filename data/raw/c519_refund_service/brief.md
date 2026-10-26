# Writer brief: c519_refund_service

Author profile `sprint_rusher`: Terse bullet fragments, many TBD markers, sections left as headings with one line.
- structure=bullets_only, english=native_sloppy, hedging=low, terminology=aliases_drift, staleness=none
- typical gaps: auth between internal services, encryption at rest, data retention, error handling
- length 400-900 words; typo rate 0.03; markdown breakage none; dangling references 0; TBD markers 2

Service: Lets merchants and support agents request, approve and track refunds of card payments. (Meridian Pay, external exposure, data: card_data, pii)

Components:
- Refunds Gateway (api_gateway)
- refund-core (service)
- refund-db (PostgreSQL) (database)
- refund-events (Kafka) (message_queue)

Flows:
- Merchant backend and support agents -> Refunds Gateway: refund requests and approvals
- Refunds Gateway -> refund-core: authenticated refund requests
- refund-core -> refund-db (PostgreSQL): refund records with payment references
- refund-core -> refund-events (Kafka): refund status events

Implementation (openapi) the document describes:
- POST /v1/refunds: Request a refund
- GET /v1/refunds/{refundId}: Retrieve a refund
- GET /v1/refunds: List refunds
- POST /v1/refunds/{refundId}/approval: Approve or reject a refund
- POST /v1/refunds/{refundId}/cancellation: Cancel a pending refund

## Planted items
- F1 [violation, critical] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Only the images of the main service are signed.
- F2 [ambiguity, high] Mention refund-db (PostgreSQL) naturally, but do NOT state: In which region the personal data of EU customers is stored and processed. Wrap the sentence(s) that mention refund-db (PostgreSQL) (the place where that information should have been) in the F2 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:RES-02|...⟧ Backups and replicas of personal data of customers in the EU should stay in regions of the EU as well.
- ⟦S:PIP-01|...⟧ Credentials of the delivery pipeline must be issued for each run and be valid for at most 1 hour.
- ⟦S:CHG-02|...⟧ Every change to production must have a rollback plan that has been tested in a pre-production environment.
- ⟦S:CAP-01|...⟧ Public endpoints must shed load with HTTP 503 instead of queueing requests when their capacity is exhausted.
- ⟦S:OBS-02|...⟧ Every service must publish its health check and error rates to the shared dashboard every minute.
- ⟦S:PRV-03|...⟧ Personal data must be used only for purposes listed in the privacy notice shown to customers at sign-up.
- ⟦S:CHG-01|...⟧ Every change to production must be reviewed by a second engineer before it is deployed.

## Functional content (no security claims)
Aim for at least 400 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.
Functional detail to describe for each endpoint:
- POST /v1/refunds: request fields payment_id, amount, currency, reason, requested_by; response fields id, payment_id, status, amount, currency
- GET /v1/refunds/{refundId}: request fields none; response fields id, payment_id, status, amount, currency
- GET /v1/refunds: request fields none; response fields id, payment_id, status, amount, currency
- POST /v1/refunds/{refundId}/approval: request fields decision, comment; response fields id, payment_id, status, amount, currency
- POST /v1/refunds/{refundId}/cancellation: request fields reason; response fields id, payment_id, status, amount, currency

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c519_refund_service/design_marked.md
