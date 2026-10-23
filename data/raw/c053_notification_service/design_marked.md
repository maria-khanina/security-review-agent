# Notification Service: stories and design

Epic: NOTIF-210 (Event-driven notifications)
Status: Ready for development
Related: NOTIF-190 (old mailer retirement, link TBD)

## Overview

The notifier consumes domain events from domain-events (Kafka), renders messages from templates and sends them through the Email and SMS provider. It also exposes an API for manual sends, template management and delivery status.

## Stories

### NOTIF-211: Send on event

As a product team, I want a message to be sent when a domain event arrives so that customers are informed without extra integration.

Acceptance criteria:
- An event on domain-events leads to exactly one notification per recipient.
- The channel follows the customer's preference.
- A failed delivery is retried with increasing delays and finally marked failed.

### NOTIF-212: Manual send and status

As a support agent, I want to send a notification manually and check its status.

Acceptance criteria:
- POST /v1/notifications accepts channel, recipient_id, template_id and locale and returns id, status and channel.
- GET /v1/notifications/{notificationId} returns the same shape.
- GET /v1/notifications lists notifications and can be filtered by channel.

### NOTIF-213: Manage templates

As a product owner, I want to change message wording without a deployment.

Acceptance criteria:
- PUT /v1/templates/{templateId} creates or replaces a template with a subject and a body.
- The newest template version for the recipient's locale is used; English is the fallback.
- A template with an unknown placeholder is rejected.

## Non-functional requirements

The following apply to every story (TBD: repeat as acceptance criteria in each ticket).

| ID | Area | Requirement |
|---|---|---|
| NFR-1 | Service authentication | ⟦S:AUTH-02|Internal service calls to the notifier are authenticated with mutual TLS or signed workload identity tokens.⟧ |
| NFR-2 | Tokens | ⟦S:AUTH-03|Access tokens expire within 15 minutes, and refresh tokens are rotated on use.⟧ |
| NFR-4 | Internal transport | ⟦S:CRYPTO-04|Traffic between services, and between services and data stores or brokers, is encrypted in transit.⟧ |
| NFR-5 | Algorithms | ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧ |
| NFR-6 | Keys | ⟦S:CRYPTO-06|Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.⟧ |
| NFR-7 | Certificates | ⟦S:CRYPTO-07|Services validate TLS certificates and never disable verification.⟧ |
| NFR-8 | Secrets in artifacts | ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ |
| NFR-9 | Secrets at runtime | ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧ |
| NFR-11 | Network | ⟦S:NET-01|Databases and message brokers sit in private subnets and are not publicly reachable.⟧ |
| NFR-12 | Egress | ⟦S:NET-04|Services that call third parties have their egress restricted to an approved allowlist.⟧ |
| NFR-13 | Security logging | ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧ |
| NFR-17 | Third parties | ⟦S:DATA-03|Personal data is sent to the Email and SMS provider only under an approved data processing agreement, and only the fields required.⟧ |
| NFR-18 | Test data | ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧ |
| NFR-19 | Callbacks | ⟦S:API-03|Provider delivery callbacks, and any outbound webhooks, are signed and the signatures are verified.⟧ |
| NFR-20 | Queries | ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧ |
| NFR-21 | Pipeline | ⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧ |
| NFR-22 | Containers | ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧ |

## Design notes

Each notification has an id, a channel, a status (queued, sent, delivered, failed) and a reference to the recipient. Contact details are looked up at send time and are not copied into the notification. De-duplication uses the notification id so that a replayed event does not produce a second message. The consumer group is committed after the provider accepts the message, which gives at-least-once behavior with de-duplication on top.

## Definition of done

- All acceptance criteria demonstrated in staging.
- OpenAPI file updated.
- Dashboard for delivery rate and provider latency (owner TBD).
