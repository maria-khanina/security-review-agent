# Writer brief: c715_notification_service

Author profile `copy_paste_veteran`: Built from an older design with find-and-replace; stale service names and sentences that contradict the new section.
- structure=clean_headings, english=native_fluent, hedging=none, terminology=aliases_drift, staleness=heavy_copy_paste
- typical gaps: which version of the auth scheme is current
- length 1400-2400 words; typo rate 0.01; markdown breakage light; dangling references 1; TBD markers 0

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
- F1 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The sandbox is a copy of the production database with names changed.
- F2 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Failed messages are retried forever and block the queue.
- F3 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The service account of the job has a password that engineers use to log in.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:VER-02|...⟧ Breaking changes of an API must be released only as a new version of the API.
- ⟦S:MSG-02|...⟧ Messages in queues must be deleted after they are processed.
- ⟦S:SUP-01|...⟧ Support agents must see card numbers and document numbers only in masked form.

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
- Save to data/raw/c715_notification_service/design_marked.md
