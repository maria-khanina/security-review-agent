# Writer brief: c013_webhook_dispatcher

Author profile `security_champion`: Long dedicated security section with many named controls, but some are aspirational and terms are used loosely.
- structure=clean_headings, english=native_fluent, hedging=none, terminology=wrong_terms, staleness=some_outdated
- typical gaps: implementation status of the controls it lists
- length 1800-2600 words; typo rate 0.0; markdown breakage light; dangling references 1; TBD markers 0

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
- F1 [ambiguity, low] Mention dispatcher naturally, but do NOT state: Whether dependencies are scanned for vulnerabilities. Wrap the sentence(s) that mention dispatcher (the place where that information should have been) in the F1 marker.
- F2 [drift, high] State as plain fact, adapted to this service: The API authenticates callers with JWT bearer tokens. Wrap the sentence(s) in the F2 marker.
- F3 [drift, medium] State as plain fact, adapted to this service: Personal data is never placed in URLs. Wrap the sentence(s) in the F3 marker.
- F4 [ambiguity, low] Mention dispatcher naturally, but do NOT state: Which algorithms protect integrity and confidentiality. Wrap the sentence(s) that mention dispatcher (the place where that information should have been) in the F4 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:API-01|...⟧ All external inputs must be validated against a schema and rejected if invalid.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:API-06|...⟧ Browser-facing APIs must allow only approved origins in CORS.

## Functional content (no security claims)
Aim for at least 1800 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c013_webhook_dispatcher/design_marked.md
