# Writer brief: c616_payment_gateway

Author profile `meeting_notes`: Written as decisions and open questions after a design meeting; some decisions are reversed later in the same doc.
- structure=meeting_notes, english=native_sloppy, hedging=high, terminology=aliases_drift, staleness=none
- typical gaps: final outcome of open questions
- length 700-1400 words; typo rate 0.03; markdown breakage light; dangling references 0; TBD markers 5

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
- F1 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Only the components that touch customer data are upgraded.
- F2 [violation, critical] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Critical vulnerabilities are fixed in the next quarterly release.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:ARC-01|...⟧ Transaction records must be kept for 7 years and must be deleted within 90 days after that period ends.
- ⟦S:TST-02|...⟧ Test accounts in production must be removed within 7 days after the test ends.
- ⟦S:NTF-01|...⟧ Messages sent to customers must not contain card numbers, passwords or images of identity documents.
- ⟦S:INV-01|...⟧ Every service must have a named owner and a named deputy in the service register.
- ⟦S:INV-02|...⟧ The service register must list for each service the personal data that it processes and every third party that receives data from it.
- ⟦S:FRD-01|...⟧ Transactions above 10,000 EUR must be held for review by the fraud team before they are settled.
- ⟦S:MON-01|...⟧ Alerts of severity high must be acknowledged within 15 minutes.

## Functional content (no security claims)
Aim for at least 700 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c616_payment_gateway/design_marked.md
