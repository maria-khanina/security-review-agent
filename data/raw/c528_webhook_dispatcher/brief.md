# Writer brief: c528_webhook_dispatcher

Author profile `diagram_narrator`: Mostly an ASCII or mermaid diagram plus short captions; flows exist only as arrows between boxes.
- structure=diagram_narration, english=jargon_dense, hedging=none, terminology=consistent, staleness=none
- typical gaps: trust boundaries, credentials on arrows, protocols on arrows
- length 500-1100 words; typo rate 0.01; markdown breakage none; dangling references 0; TBD markers 0

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
- F1 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The gateway holds requests for up to a minute when the service is slow.
- F2 [ambiguity, low] Mention dispatcher naturally, but do NOT state: Whether changes to production have a tested rollback plan. Wrap the sentence(s) that mention dispatcher (the place where that information should have been) in the F2 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:PIP-01|...⟧ Credentials of the delivery pipeline must be issued for each run and be valid for at most 1 hour.
- ⟦S:PIP-02|...⟧ Build artifacts must be signed, and the signature must be verified before deployment.
- ⟦S:CHG-01|...⟧ Every change to production must be reviewed by a second engineer before it is deployed.
- ⟦S:OBS-02|...⟧ Every service must publish its health check and error rates to the shared dashboard every minute.

## Functional content (no security claims)
Aim for at least 500 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c528_webhook_dispatcher/design_marked.md
