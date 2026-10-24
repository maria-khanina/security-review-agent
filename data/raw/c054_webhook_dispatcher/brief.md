# Writer brief: c054_webhook_dispatcher

Author profile `ticket_writer`: Jira style with user stories, numbered requirements and acceptance criteria; non-functional requirements are afterthoughts.
- structure=ticket_style, english=native_fluent, hedging=low, terminology=consistent, staleness=none
- typical gaps: security as acceptance criteria, data classification
- length 900-1700 words; typo rate 0.0; markdown breakage none; dangling references 0; TBD markers 0

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
- F1 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): CORS is set to allow all origins to unblock the frontend team.
- F2 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Dynamic queries are assembled with string formatting because the ORM is too slow.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTH-01|...⟧ Every externally reachable API endpoint must authenticate callers with OAuth2/OIDC bearer tokens or mutual TLS.
- ⟦S:AUTHZ-01|...⟧ Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.
- ⟦S:OPS-02|...⟧ Containers must run as a non-root user with a read-only root filesystem where possible.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:NET-05|...⟧ External APIs must sit behind a WAF with rate limiting.
- ⟦S:CRYPTO-04|...⟧ Traffic between services and to data stores must be encrypted in transit.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:API-01|...⟧ All external inputs must be validated against a schema and rejected if invalid.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.

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
- Save to data/raw/c054_webhook_dispatcher/design_marked.md
