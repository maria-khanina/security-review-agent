# Writer brief: c518_refund_service

Author profile `methodical_architect`: Thorough and tidy, but works at a high level of abstraction and skips operational details.
- structure=clean_headings, english=native_fluent, hedging=low, terminology=consistent, staleness=none
- typical gaps: secret rotation, key ownership, who can query the database directly, logging of sensitive fields
- length 1800-2600 words; typo rate 0.0; markdown breakage none; dangling references 0; TBD markers 0

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
- F1 [violation, critical] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Only one engineer knows where the kill switch is.
- F2 [violation, critical] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Database migrations cannot be rolled back, and nothing is planned for that.
- F3 [ambiguity, high] Mention Refunds Gateway naturally, but do NOT state: What happens to requests when the capacity of a public endpoint is exhausted. Wrap the sentence(s) that mention Refunds Gateway (the place where that information should have been) in the F3 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:PIP-01|...⟧ Credentials of the delivery pipeline must be issued for each run and be valid for at most 1 hour.
- ⟦S:OBS-01|...⟧ Traces and metrics must not contain personal data or card data.

## Functional content (no security claims)
Aim for at least 1800 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c518_refund_service/design_marked.md
