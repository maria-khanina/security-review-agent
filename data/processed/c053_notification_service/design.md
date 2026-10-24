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
| NFR-1 | Service authentication | Service-to-service calls are authenticated, either with mutual TLS between the workloads or with a signed workload identity token. |
| NFR-2 | Tokens | Access tokens stay valid for a week, so the calling services do not have to renew them often. |
| NFR-4 | Internal transport | Traffic between services, and between services and data stores or brokers, is encrypted in transit. |
| NFR-5 | Algorithms | Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not. |
| NFR-6 | Keys | KMS holds the keys, the data stores only keep ciphertext, and key rotation happens at least yearly. |
| NFR-7 | Certificates | TLS certificate verification is enabled in all clients, with no option to disable it. |
| NFR-8 | Secrets in artifacts | Secrets do not appear in source code, configuration files, specifications or infrastructure definitions. |
| NFR-9 | Secrets at runtime | Runtime secrets are fetched from the approved secret store at startup. |
| NFR-11 | Network | Databases and message brokers sit in private subnets and are not publicly reachable. |
| NFR-12 | Egress | The sender follows redirects and calls any host, and there is no allow-list. |
| NFR-13 | Security logging | We log failed logins, changes of privileges and reads of sensitive data. |
| NFR-17 | Third parties | No personal data leaves for a third party without an approved DPA, and the payload is limited to the required fields. |
| NFR-18 | Test data | Test and staging environments use synthetic data, never real personal data or card data. |
| NFR-19 | Callbacks | Inbound and outbound webhooks include an HMAC signature and a timestamp; verification of both is mandatory on the receiving side. |
| NFR-20 | Queries | Database queries are parameterized, and user input is never concatenated into SQL. |
| NFR-21 | Pipeline | CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days. |
| NFR-22 | Containers | Containers run as a non-root user, with a read-only root filesystem where possible. |

Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.
Reports and exports with personal data are available only to authorized users, stored encrypted, and deleted after 7 days.
Requests from outside are checked against the schema and rejected if they do not conform.
Admin and debug endpoints are reachable only from the internal network, not from the public internet.
Internal details such as stack traces, SQL and hostnames never appear in an error response.
Reading centralized logs requires authorization, and only approved staff have it.

## Design notes

Each notification has an id, a channel, a status (queued, sent, delivered, failed) and a reference to the recipient. Contact details are looked up at send time and are not copied into the notification. De-duplication uses the notification id so that a replayed event does not produce a second message. The consumer group is committed after the provider accepts the message, which gives at-least-once behavior with de-duplication on top.

## Definition of done

- All acceptance criteria demonstrated in staging.
- OpenAPI file updated.
- Dashboard for delivery rate and provider latency (owner TBD).
