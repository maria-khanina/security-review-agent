# Notification Platform: Product and Design Overview

Owner: Product & Growth, Customer Experience Pod
Status: Approved for build

## 1. Vision

Customers expect to hear from us at exactly the right moment: when a payment lands, when a transfer is blocked, when a statement is ready. Today every team sends its own messages in its own way, which creates an inconsistent experience and a lot of duplicated effort. The Notification Platform gives Meridian Pay one enterprise-grade, secure-by-design channel for email, SMS and push messages, so product teams can focus on the moment and not on the plumbing.

Success for the first release means three things: every domain event that should produce a message produces exactly one, messages reach the customer within seconds, and any product team can change wording without a code release.

## 2. Customer value

- Customers get consistent, timely and localized messages in the channel they prefer.
- Product teams get a single place to manage templates and see delivery status.
- Operations gets one dashboard instead of five, which shortens incident response.
- Finance gets predictable provider costs because volumes flow through one contract.

## 3. Scope

In scope for release one: transactional notifications triggered by domain events, template management, delivery status lookups and a history of what was sent. Out of scope for now: marketing campaigns, in-app inbox, rich media and scheduled digests. These are on the roadmap for later quarters and will reuse the same building blocks.

## 4. Architecture overview

Domain events arrive on the shared event stream (domain-events, Kafka). The notifier service reads each event, decides which template and channel apply, renders the message and hands it to our email and SMS provider for delivery. Delivery results come back to the notifier, which keeps a history that product and support teams can query.

There are only three moving parts: the event stream, the notifier and the external provider. We deliberately kept the design small so it is easy to explain, easy to test and easy to extend.

## 5. Capabilities

**Send a notification.** POST /v1/notifications accepts a channel, a recipient identifier, a template identifier and a locale. It returns a receipt with an identifier, a status and the channel used. Product services call it directly when a message must go out outside the event flow, for example a manual resend requested by support.

**Check delivery status.** GET /v1/notifications/{notificationId} returns the same receipt shape so teams can follow a message from queued to delivered or failed.

**Manage templates.** PUT /v1/templates/{templateId} creates or replaces a template. A template has a subject and a body, and the platform keeps one version per locale. Changing a template takes effect for the next message without a deployment.

**Browse history.** GET /v1/notifications lists receipts and can be narrowed by channel. Support uses it to answer the question every customer eventually asks: did you actually send me that message?

## 6. Data model

A notification has an identifier, a channel, a status and a reference to the recipient. A template has an identifier, a subject and a body. Recipients are referenced by identifier; contact details are looked up at send time. Statuses move through queued, sent, delivered and failed, and a failed message can be retried by the same identifier.

## 7. Reliability and quality

The platform is designed for at-least-once delivery, with de-duplication on the notification identifier so customers do not receive the same message twice. If the provider is slow or unavailable, the notifier retries with increasing delays and finally marks the message failed so a human can look at it. Templates are validated before they are accepted, so a typo in a placeholder cannot reach customers.

## 8. Security and compliance posture

Security is a first-class feature of this platform, not an afterthought. The principles below are the commitments we make to our customers and to the compliance team.

- The approved algorithm list is followed, and MD5, SHA-1, DES, 3DES and ECB mode are prohibited in this service.
- The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only.
- Source, config, specs and infrastructure definitions contain no secrets. At startup the service fetches its secrets from the approved secret store.

Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
Connections to the database and between internal services use TLS.

External inputs are accepted only if they validate against the schema.
- The audit trail includes authentication failures, privilege changes and sensitive-data access. Logs contain no secrets, card numbers or personal data beyond opaque identifiers.
- Third parties receive only the fields they need, and only if an approved data processing agreement covers them.
- Any authenticated caller can fetch a message record or a delivery status if it knows the identifier, since ids are random and we do not compare them with an owner.
- We use parameterized queries only, with no SQL built from user input by string concatenation.
- Dependency scanning does not exist yet and the versions of the libraries were pinned a long time ago, so nobody looks at vulnerabilities.
- The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.

## 9. Analytics and reporting

Product leaders asked for self-service delivery analytics from day one. To avoid building a reporting layer ourselves in release one, the external BI vendor connects directly to the notification history database through a public database endpoint that we keep open for them. Dashboards for open rates, delivery rates and channel mix are built on their side from that data. We expect to revisit this in a later release once the analytics team has settled on a long-term tool.

## 10. Rollout

Rollout happens in three waves. Wave one covers payment confirmations for a small share of customers in one market. Wave two adds transfer and card alerts. Wave three opens the send endpoint to the remaining product teams. After each wave the team reviews delivery rates, complaint rates and provider cost before moving on. A feature flag lets us roll back a channel instantly.

## 11. Open questions

- Which locales ship in wave one? Product favors English and German only.
- Do we need quiet hours per market? Legal is checking.
- Who owns template review: Product or Brand?
- Provider cost alerts: do we want a budget threshold?
