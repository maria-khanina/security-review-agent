# Writer brief: c729_webhook_dispatcher

Author profile `stream_of_consciousness`: Long unbroken paragraphs written as thinking aloud, flows described in the order they came to mind.
- structure=wall_of_text, english=native_sloppy, hedging=high, terminology=aliases_drift, staleness=none
- typical gaps: explicit statement of authentication method, which component stores what
- length 900-1800 words; typo rate 0.03; markdown breakage none; dangling references 0; TBD markers 2

Service: Delivers signed event callbacks to merchant endpoints with retries. (Meridian Pay, external exposure, data: internal)

Components:
- dispatcher (service)
- delivery-queue (message_queue)
- Merchant callback endpoints (third_party)

Flows:
- Platform services -> dispatcher: events to deliver
- dispatcher -> delivery-queue: pending deliveries
- dispatcher -> Merchant callback endpoints: signed event payloads

Implementation (openapi) the document describes:
- POST /v1/subscriptions: Register a callback endpoint
- GET /v1/subscriptions/{subscriptionId}: Retrieve a subscription
- POST /v1/subscriptions/{subscriptionId}/rotate-secret: Rotate the signing secret
- GET /v1/deliveries: List delivery attempts
- POST /v1/deliveries/{deliveryId}/replay: Replay a delivery

## Planted items
- F1 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Only the payment endpoint is idempotent, transfers are not.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:REC-01|...⟧ Balances must be reconciled with the ledger every day, and a difference of more than 0.01 EUR must be reported to the finance team within 24 hours.
- ⟦S:VER-01|...⟧ A replaced version of an API must be kept for 12 months, and its removal must be announced 90 days in advance.
- ⟦S:VER-02|...⟧ Breaking changes of an API must be released only as a new version of the API.
- ⟦S:MSG-01|...⟧ Messages that cannot be processed must be moved to a dead-letter queue and be examined within one working day.
- ⟦S:MSG-02|...⟧ Messages in queues must be deleted after they are processed.

## Functional content (no security claims)
Aim for at least 900 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.
Functional detail to describe for each endpoint:
- POST /v1/subscriptions: request fields url, event_types, description; response fields id, url, status
- GET /v1/subscriptions/{subscriptionId}: request fields none; response fields id, url, status
- POST /v1/subscriptions/{subscriptionId}/rotate-secret: request fields grace_period_hours; response fields id, url, status
- GET /v1/deliveries: request fields none; response fields id, event_type, status, attempts
- POST /v1/deliveries/{deliveryId}/replay: request fields reason; response fields id, event_type, status, attempts

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c729_webhook_dispatcher/design_marked.md
