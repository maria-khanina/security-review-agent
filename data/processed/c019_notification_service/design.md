# Notification Service Design

Based on the mailer service design (v1) and the "notification worker" proposal. Sections copied from those documents are marked where the names differ.

## 1. Background

The mailer service (mailer-svc in the old runbooks, "the notifier" in the newer ones, notification worker in the proposal) sends email and SMS messages for the payment platform. This document replaces the older versions. Where the older text referred to Sendgrid, the new text refers to the Email and SMS provider; the provider contract was changed last year and the old name still appears in some dashboards.

## 2. Components

- **domain-events (Kafka):** the topic with events that trigger messages. In the v1 text this was a database table polled every minute. That is no longer the case.
- **notifier:** reads events, picks a template, renders the message, sends it to the provider and records the delivery status.
- **Email and SMS provider:** the external service that delivers messages.

## 3. API

- POST /v1/notifications sends a notification. Fields: channel, recipient_id, template_id and locale. The reply has id, status and channel.
- GET /v1/notifications/{notificationId} returns the delivery status in the same shape.
- PUT /v1/templates/{templateId} creates or replaces a template (subject and body) and returns it.
- GET /v1/notifications lists notifications; it can be filtered by channel.

## 4. How a message is sent

An event arrives on domain-events. The notifier maps the event type to a template, fills in the placeholders and chooses the channel from the customer's preference. The notifier then hands the rendered message over to the provider for delivery and waits for the delivery report. If the provider reports a failure, the notifier retries a few times with growing delays and finally marks the notification failed. The v1 document said "three retries"; the current setting is five, and the table in section 8 shows the current value.

## 5. Templates

Templates have a subject and a body with placeholders. A template is versioned and the notifier always uses the newest version for a locale. Missing locales fall back to English. The v1 text described templates stored as files in the repository; they are now stored through the template endpoint.

## 6. Security

This section is carried over from the mailer design and updated.

- Calls between our own services carry a signed workload identity token or use mutual TLS, and the receiving service checks it.
- Administrative and debug endpoints must not be reachable from the public internet.
- Access tokens live for at most 15 minutes, and every refresh token is replaced when it is used.
- Staff roles are limited to what each job needs, and every service defines its own roles.
- The approved secret manager is the only source of runtime secrets, fetched at start-up.
- A caller can only read or change resources that belong to them or that they have been explicitly granted.
- Production access rights are reviewed every quarter.
- Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.
- No secrets are kept in source code, config files, API specs or infrastructure definitions.
- The database and the message broker are in private subnets with no public address.
- Access to the log platform is given to whole teams and nobody removes it when people change role.
- Connections to the database and between internal services use TLS.
- The service collects and stores only the personal data needed to deliver messages.
- Reports and exports with personal data are available only to authorized users, stored encrypted, and deleted after 7 days.
- Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year.
- Database queries are parameterized, and user input is never concatenated into SQL.

## 7. Logging, build and operations

- Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.
- We scrub logs so that they contain neither secrets, card numbers nor personal data other than opaque identifiers.
- Audit entries share the application log group and expire after thirty days. This is the same group the v1 service used, and the setting was not changed during the migration.
- Container images are never rescanned after the first build. The build pipeline is the one used for the mailer; it builds an image on every merge and publishes it.

## 8. Operational values

| Setting | Current value | Value in v1 text |
|---|---|---|
| Provider retries | 5 | 3 |
| Retry delay start | 10 seconds | 30 seconds |
| Template cache lifetime | 60 seconds | none |
| Kafka consumer group | notifier-main | mailer-group |

## 9. Deployment

The notifier runs as two replicas. The v1 document said one replica with a hot standby; the standby was dropped when Kafka consumer groups were introduced. A rolling update replaces one replica at a time and the consumer group rebalances automatically. The runbook still has a section on switching to the standby; that section is obsolete and will be removed.

## 10. Open items

- Rename leftover dashboards from mailer-svc to notifier.
- Remove the obsolete standby section from the runbook.
- Decide whether to keep the 60-second template cache.
