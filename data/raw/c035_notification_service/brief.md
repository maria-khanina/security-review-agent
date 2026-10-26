# Writer brief: c035_notification_service

Author profile `copy_paste_veteran`: Built from an older design with find-and-replace; stale service names and sentences that contradict the new section.
- structure=clean_headings, english=native_fluent, hedging=none, terminology=aliases_drift, staleness=heavy_copy_paste
- typical gaps: which version of the auth scheme is current
- length 1400-2400 words; typo rate 0.0; markdown breakage none; dangling references 3; TBD markers 0

Service: Sends email, SMS and push notifications triggered by domain events. (Meridian Pay, internal exposure, data: pii, internal)

Components:
- notifier (service)
- domain-events (Kafka) (message_queue)
- Email and SMS provider (third_party)

Flows:
- domain-events (Kafka) -> notifier: events that trigger messages
- notifier -> Email and SMS provider: recipient contact details and message body

Implementation (openapi) the document describes:
- POST /v1/notifications: Send a notification
- GET /v1/notifications/{notificationId}: Get delivery status
- PUT /v1/templates/{templateId}: Create or replace a template
- GET /v1/notifications: List notifications

## Planted items
- F1 [ambiguity, low] Mention notifier naturally, but do NOT state: What data is shared with the vendor and under what agreement. Wrap the sentence(s) that mention notifier (the place where that information should have been) in the F1 marker.
- F2 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Roles are defined globally for all services rather than per service, and nobody reviews them.
- F3 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Security-relevant events are not separated from normal logs and are not monitored.
- F4 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The profile table keeps every attribute the mobile app can send.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:DATA-05|...⟧ Reports and exports containing personal data must require authorization, be encrypted in storage and expire.
- ⟦S:AUTHZ-01|...⟧ Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:LOG-04|...⟧ Access to centralized logs must be limited to authorized staff.
- ⟦S:LOG-03|...⟧ Audit logs must be tamper-evident and retained for at least one year.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.

## Functional content (no security claims)
Aim for at least 1400 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.
Functional detail to describe for each endpoint:
- POST /v1/notifications: request fields channel, recipient_id, template_id, locale; response fields id, status, channel
- GET /v1/notifications/{notificationId}: request fields none; response fields id, status, channel
- PUT /v1/templates/{templateId}: request fields subject, body; response fields id, subject, body
- GET /v1/notifications: request fields none; response fields id, status, channel

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c035_notification_service/design_marked.md
