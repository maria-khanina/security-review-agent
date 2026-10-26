# Writer brief: c079_notification_service

Author profile `security_champion`: Long dedicated security section with many named controls, but some are aspirational and terms are used loosely.
- structure=clean_headings, english=native_fluent, hedging=none, terminology=wrong_terms, staleness=some_outdated
- typical gaps: implementation status of the controls it lists
- length 1800-2600 words; typo rate 0.0; markdown breakage none; dangling references 0; TBD markers 0

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
- F1 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Sensitive fields are encrypted with AES in ECB mode for simplicity.
- F2 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Any authenticated caller can read any record if it knows the identifier.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:LOG-04|...⟧ Access to centralized logs must be limited to authorized staff.
- ⟦S:AUTHZ-02|...⟧ Internal users must receive only the roles required for their job and roles must be defined per service.
- ⟦S:AUTHZ-05|...⟧ Access rights to production systems must be reviewed at least quarterly.
- ⟦S:API-01|...⟧ All external inputs must be validated against a schema and rejected if invalid.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:DATA-05|...⟧ Reports and exports containing personal data must require authorization, be encrypted in storage and expire.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:CRYPTO-04|...⟧ Traffic between services and to data stores must be encrypted in transit.
- ⟦S:AUTH-03|...⟧ Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- ⟦S:LOG-03|...⟧ Audit logs must be tamper-evident and retained for at least one year.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:CRYPTO-06|...⟧ Encryption keys must be held in KMS, never stored with the data they protect, and rotated at least annually.

## Functional content (no security claims)
Aim for at least 1800 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c079_notification_service/design_marked.md
