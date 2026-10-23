# Writer brief: c001_notification_service

Author profile `table_lover`: Everything in tables (components, endpoints, data stores); prose is minimal and some tables are malformed.
- structure=tables_only, english=jargon_dense, hedging=none, terminology=consistent, staleness=none
- typical gaps: reasons and conditions that do not fit a table cell
- length 600-1300 words; typo rate 0.01; markdown breakage light; dangling references 0; TBD markers 0

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
- F1 [drift, medium] State as plain fact, adapted to this service: The API enforces per-client rate limits. Wrap the sentence(s) in the F1 marker.
- F2 [violation, medium] State, as the author naturally would and believing it acceptable: Full request bodies logged for debugging including emails and card numbers.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:AUTHZ-02|...⟧ Internal users must receive only the roles required for their job and roles must be defined per service.
- ⟦S:AUTHZ-05|...⟧ Access rights to production systems must be reviewed at least quarterly.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:DATA-01|...⟧ Services must collect and store only the personal data needed for their purpose.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:DATA-05|...⟧ Reports and exports containing personal data must require authorization, be encrypted in storage and expire.

## Functional content (no security claims)
Aim for at least 600 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c001_notification_service/design_marked.md
