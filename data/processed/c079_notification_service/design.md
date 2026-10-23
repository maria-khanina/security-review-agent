# Notification Service: Architecture and Security Control Catalogue

Author: Rina M., Security Champion, Customer Communications
Review: Security Architecture
Revision: 4 (revision 3 called the notifier "mailer-svc"; the old name is retired but still appears in some dashboards)

## 1. Summary

The notification service delivers email and SMS messages for the payment platform. It consumes domain events, renders messages from templates and sends them through an external Email and SMS provider. Messages contain personal data, so the controls of the service are catalogued here in detail. Reviewers should read the catalogue (section 5) first and the architecture afterwards.

## 2. Architecture

Domain events arrive on domain-events (Kafka). The notifier reads each event, chooses a template and a channel, renders the message and hands it to the Email and SMS provider. Delivery reports come back to the notifier, which keeps a history that product and support can query. The three parts are the event stream, the notifier and the provider; there is no other service in the path.

## 3. API

- POST /v1/notifications sends a notification (channel, recipient_id, template_id, locale) and returns id, status and channel.
- GET /v1/notifications/{notificationId} returns the delivery status.
- PUT /v1/templates/{templateId} creates or replaces a template (subject and body) and returns it.
- GET /v1/notifications lists notifications and can be filtered by channel.

## 4. Message handling

The notifier maps each event type to a template and takes the channel from the customer's preference. A failed delivery is retried with growing delays and finally marked failed. A notification identifier makes sends idempotent, so a replayed event does not produce a second message. Templates are versioned per locale; English is the fallback. (Revision 3 described a fixed set of three retries and a template store in files; both were replaced.)

## 5. Control catalogue

Control identifiers (N-1 and so on) match the compliance spreadsheet (link TBD; the older spreadsheet is stale).

### 5.1 Identity and access

- N-1: Internal service calls to the notifier are authenticated with mutual TLS or signed workload identity tokens.
- N-2: Internal users receive only the roles required for their job, and roles are defined per service.
- N-3: Access to production is recertified at least once per quarter.

### 5.2 Data protection

- N-4: Personal data is never placed in URLs.
- N-5: Sensitive fields are encrypted with AES in ECB mode for simplicity.
- N-6: No personal data leaves for a third party without an approved DPA, and the payload is limited to the required fields.
- N-7: Delivery reports that contain personal data require authorization to access, are encrypted in storage and expire.

### 5.3 Secrets and network

- N-8: Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- N-10: Databases and message brokers sit in private subnets and are not publicly reachable.

### 5.4 Logging

- N-11: We log failed logins, changes of privileges and reads of sensitive data.

### 5.5 Application security and operations

- N-13: User input reaches the database only as query parameters, never as part of the query text.

## 6. Template safety

Templates accept only a fixed list of placeholders. A template with an unknown placeholder is rejected when it is saved, and placeholder values are inserted as plain text, never evaluated. The template body is limited in size. These rules keep a faulty template from producing a faulty message at scale.

## 7. Delivery details

The notifier keeps the provider's message identifier with each notification, so that delivery reports can be matched. Reports that arrive for an unknown identifier are set aside for investigation. SMS messages longer than the carrier limit are split by the provider and reported as one delivery. Email messages carry a plain-text part for clients that do not render markup.

## 8. Capacity and deployment

The expected volume is several hundred thousand messages a day with peaks at month end. The notifier runs as two replicas that share a Kafka consumer group (revision 3 said one instance plus a cold standby; the standby was dropped). Rolling updates replace one replica at a time. The provider's rate limits are respected by a token bucket in the notifier.

## 9. Open items

- Status column of the catalogue: controls are listed without an implementation status; the spreadsheet carries it (link TBD).
- The provider's delivery report format changes next quarter; the adapter will need an update.
- See also the archived page for the mailer design (link may not open).
