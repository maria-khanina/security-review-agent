# Notification Service Design

Merged from: mailer-service design v1 (2021), notification worker proposal (2022), and the 2023 platform migration notes. Passages from older documents keep their original names; see section 9 for a name mapping.

## 1. Overview

The notification service (the mailer in v1, the worker in the proposal, the notifier in the platform notes) delivers email and SMS messages for the payment platform. It consumes events, renders messages from templates and hands them to the delivery provider. This revision updates the 2023 notes with the current Kafka-based design; where the v1 text described polling a database table, that description no longer applies.

## 2. Components

- **domain-events (Kafka).** Carries the events that trigger messages. (v1: the `events` table in the shared database; the table still exists but is no longer read.)
- **notifier.** Reads the events, selects a template and channel, renders the message, calls the provider and records the status. (v1: mailer-svc; proposal: notification worker.)
- **Email and SMS provider.** External service that delivers the messages. (v1: Sendgrid; the contract was replaced in 2022.)

## 3. API

- POST /v1/notifications sends a notification. Fields: channel, recipient_id, template_id, locale. Reply: id, status, channel.
- GET /v1/notifications/{notificationId} returns the delivery status.
- PUT /v1/templates/{templateId} creates or replaces a template; fields subject and body.
- GET /v1/notifications lists notifications and can be filtered by channel.

The v1 document listed a fifth endpoint, DELETE /v1/notifications/{id}, which was removed in 2022. The older clients that still call it receive a not-found reply.

## 4. Message flow

An event arrives on domain-events. The notifier maps the event type to a template and a channel, using the customer's channel preference. The notifier then passes the rendered message to the provider for delivery and records the delivery report when the provider sends it. A failed delivery is retried with growing delays; after five attempts the status becomes failed. The v1 text said three attempts and a fixed delay of thirty seconds, which was changed in 2023.

## 5. Templates

A template has a subject and a body with placeholders and is stored per locale. The notifier uses the newest version of the template for the recipient's locale and falls back to English. The v1 document stored templates as files in the service repository; that was replaced by the template endpoint above. The proposal document suggested a template approval step; it was never built.

## 6. Security

This section combines the v1 security section with the 2023 updates.

- Calls between internal services and the notifier are authenticated with mutual TLS or signed workload identity tokens. (The v1 text relied on a shared header; this was replaced during the migration.)
- Roles are defined once, globally, for all platform services rather than per service, and every service reuses the same set.
- Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- Databases and message brokers are not publicly reachable and live in private subnets.
- The service collects and stores only the personal data needed to deliver messages.
- Delivery reports that contain personal data require authorization to access, are encrypted in storage and expire.
- Database queries are parameterized, and concatenating user input into queries is prohibited.

## 7. Logging

- Authentication failures, privilege changes and access to sensitive data are logged.

## 8. Build and deployment

The service runs as two replicas. The v1 document described a single instance with a cold standby, and the proposal described a pool of workers; the current deployment is two identical replicas that share a Kafka consumer group. Rolling updates replace one replica at a time. Jenkins was used for builds in v1; builds now run in the shared CI platform.

## 9. Name mapping

| Current name | v1 name | Proposal name |
|---|---|---|
| notifier | mailer-svc | notification worker |
| domain-events | events table | event queue |
| Email and SMS provider | Sendgrid | delivery vendor |

## 10. Open items

- Remove the leftover mailer dashboards (see the ticket under the old project key, link may be dead).
- Decide whether to restore the template approval step from the proposal.
- Confirm the retry settings in the runbook; the runbook still shows the v1 values.
