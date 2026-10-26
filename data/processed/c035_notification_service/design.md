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

Runtime secrets must be fetched from the approved secret store at startup.
- Roles are defined once, globally, for all platform services rather than per service, and every service reuses the same set.
- We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.
- Audit logs are written to tamper-evident storage with at least one year of retention.
- Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.
- Data stores and brokers sit in private subnets only.
- The profile table of the notifier keeps every attribute that the calling services send.
- Each export file is encrypted at rest, readable only by the authorized requester, and removed automatically after 72 hours.
- Ownership is verified on every access to customer-owned data, not only at login.
- All queries use bound parameters instead of string concatenation.

## 7. Logging

- Security-relevant events are not separated from normal logs, and nobody monitors them.
- Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids.
- Access to centralized logs must be limited to authorized staff.

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
