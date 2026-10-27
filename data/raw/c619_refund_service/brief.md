# Writer brief: c619_refund_service

Author profile `ticket_writer`: Jira style with user stories, numbered requirements and acceptance criteria; non-functional requirements are afterthoughts.
- structure=ticket_style, english=native_fluent, hedging=low, terminology=consistent, staleness=none
- typical gaps: security as acceptance criteria, data classification
- length 900-1700 words; typo rate 0.01; markdown breakage light; dangling references 1; TBD markers 0

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
- F1 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Versions of components are not recorded anywhere outside the build files.
- F2 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Ownership is shared by three people, so nobody feels responsible.
- F3 [ambiguity, high] Mention refund-core naturally, but do NOT state: How long transaction records are kept and who removes them afterwards. Wrap the sentence(s) that mention refund-core (the place where that information should have been) in the F3 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:ARC-02|...⟧ Documents uploaded by customers must be deleted within 30 days after the account is closed.
- ⟦S:VUL-01|...⟧ Vulnerabilities rated critical must be fixed in production within 7 days after they are published.
- ⟦S:TST-01|...⟧ Production data must not be copied to test or development environments.
- ⟦S:TST-02|...⟧ Test accounts in production must be removed within 7 days after the test ends.
- ⟦S:INV-02|...⟧ The service register must list for each service the personal data that it processes and every third party that receives data from it.
- ⟦S:FRD-01|...⟧ Transactions above 10,000 EUR must be held for review by the fraud team before they are settled.
- ⟦S:MON-01|...⟧ Alerts of severity high must be acknowledged within 15 minutes.

## Functional content (no security claims)
Aim for at least 900 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c619_refund_service/design_marked.md
