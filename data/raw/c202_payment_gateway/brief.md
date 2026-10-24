# Writer brief: c202_payment_gateway

Author profile `buzzword_pm`: Business framing, security stated as adjectives ("enterprise-grade", "secure by design") with no mechanisms.
- structure=clean_headings, english=native_fluent, hedging=none, terminology=wrong_terms, staleness=none
- typical gaps: every concrete control, algorithms, token lifetimes, network boundaries
- length 900-1600 words; typo rate 0.0; markdown breakage none; dangling references 1; TBD markers 0

Service: Accepts card payments from merchants, routes to acquirers, publishes payment events. (Meridian Pay, external exposure, data: card_data, pii)

Components:
- Payments Edge Gateway (api_gateway)
- payments-core (service)
- payments-db (PostgreSQL) (database)
- Acquirer connector (third_party)
- payment-events (Kafka) (message_queue)

Flows:
- Merchant backend -> Payments Edge Gateway: payment request with card token
- Payments Edge Gateway -> payments-core: validated payment request
- payments-core -> payments-db (PostgreSQL): payment records
- payments-core -> Acquirer connector: authorization request
- payments-core -> payment-events (Kafka): payment status events

Implementation (openapi) the document describes:
- POST /v1/payments: Create a payment
- GET /v1/payments/{paymentId}: Retrieve a payment
- POST /v1/payments/{paymentId}/capture: Capture an authorized payment
- POST /v1/payments/{paymentId}/refunds: Refund a payment
- GET /v1/payments: List payments

## Planted items
- F1 [violation, critical] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The amount and the currency are taken from the client request without comparing them with the stored order.
- F2 [ambiguity, high] Mention Payments Edge Gateway naturally, but do NOT state: Whether payment operations carry an idempotency key and what happens when a request is repeated. Wrap the sentence(s) that mention Payments Edge Gateway (the place where that information should have been) in the F2 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:PAY-02|...⟧ Refunds and reversals above 1,000 EUR must be approved by a second person, and the person who requested the operation must not be able to approve it.
- ⟦S:TEN-02|...⟧ Tenant data in shared storage should be separated by row-level security or by tenant-specific encryption keys.
- ⟦S:DR-01|...⟧ Databases must have point-in-time recovery enabled with at least seven days of retention.
- ⟦S:TPC-01|...⟧ Every third-party SDK or library must be approved before its first use, and the list of approved components must be reviewed every six months.

## Functional content (no security claims)
Aim for at least 900 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.
Functional detail to describe for each endpoint:
- POST /v1/payments: request fields amount, currency, card_token, merchant_id, reference; response fields id, status, amount, currency, last4, merchant_id
- GET /v1/payments/{paymentId}: request fields none; response fields id, status, amount, currency, last4, merchant_id
- POST /v1/payments/{paymentId}/capture: request fields amount; response fields id, status, amount, currency, last4, merchant_id
- POST /v1/payments/{paymentId}/refunds: request fields amount, reason; response fields id, status, amount
- GET /v1/payments: request fields none; response fields id, status, amount, currency, last4, merchant_id

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c202_payment_gateway/design_marked.md
