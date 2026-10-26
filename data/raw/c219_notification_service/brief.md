# Writer brief: c219_notification_service

Author profile `sprint_rusher`: Terse bullet fragments, many TBD markers, sections left as headings with one line.
- structure=bullets_only, english=native_sloppy, hedging=low, terminology=aliases_drift, staleness=none
- typical gaps: auth between internal services, encryption at rest, data retention, error handling
- length 400-900 words; typo rate 0.01; markdown breakage none; dangling references 0; TBD markers 2

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
- F1 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The procedure was written for the old monolith and was never updated.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:TPC-01|...⟧ Every third-party SDK or library must be approved before its first use, and the list of approved components must be reviewed every six months.
- ⟦S:DR-02|...⟧ The recovery time objective of a critical service must not exceed 4 hours, and it must be proven by a failover exercise at least once a year.

## Functional content (no security claims)
Aim for at least 400 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c219_notification_service/design_marked.md
