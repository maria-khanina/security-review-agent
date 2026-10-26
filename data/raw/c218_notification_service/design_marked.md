# Notification Service: Design

Owner: Customer Communication team
Status: approved for build

## 1. Background and goals

Notifications are sent today by several modules of the monolith, each with its own templates and its own way of choosing the channel. The Notification Service collects this in one place. It receives domain events from the platform, chooses the channel and the template, renders the message and hands it to the provider that delivers email and SMS. The goals are one set of templates for all messages, a consistent delivery status for every message and the freedom to change the provider without changing the callers.

## 2. Non-goals

- Marketing campaigns are not sent from this service.
- The service does not decide which events should produce a message; the producing team decides and registers the event type.
- In-app inboxes are not part of this release.

## 3. Architecture

The notifier is the only component of the service. It reads events from the domain-events topic (Kafka), looks up the template for the event type and the locale of the recipient, fills in the placeholders and sends the result to the Email and SMS provider. The provider reports the delivery result back, and the notifier stores the status.

⟦F2|The notifier runs as two replicas that share a Kafka consumer group, and a rolling update replaces one replica at a time.⟧

## 4. Interfaces

**POST /v1/notifications** sends a notification that is not tied to an event. The request carries channel, recipient_id, template_id and locale; the response returns id, status and channel.

**GET /v1/notifications/{notificationId}** returns the delivery status with id, status and channel. The statuses are `queued`, `sent`, `delivered` and `failed`.

**PUT /v1/templates/{templateId}** creates or replaces a template. The request carries subject and body, and the response returns id, subject and body. Templates contain placeholders in double braces that the notifier fills from the event.

**GET /v1/notifications** lists notifications with the same fields as the status call, in pages.

## 5. Behavior

A message is sent once per event. When the provider reports a temporary failure, the notifier retries after one minute, five minutes and fifteen minutes; after the third retry the status is `failed`. Messages to the same recipient for the same event type are merged when they arrive within one minute of each other, so that a customer does not receive three SMS for three small changes.

The locale of the recipient decides the template. If no template exists for the locale, the notifier uses the English one and records the fallback.

## 6. Third-party components

The notifier uses the SDK of the provider and a few libraries for template rendering and Kafka access. ⟦F1|Third-party components are approved when a team asks to add them, and components that arrive as dependencies of approved libraries are not checked.⟧

⟦S:IR-02|For security incidents we keep a runbook for this service and a paged on-call owner, and we rehearse the runbook at least twice a year.⟧

## 7. Rollout

The service goes live in three steps: transaction messages first, then account messages and last the reminders. The old modules keep sending in parallel for two weeks per step; a comparison job reports differences. After a step is complete, the old sending code is removed. See the migration plan in the appendix for the order of the event types.

## 8. Open questions

- Whether delivery receipts from the provider should be kept for longer than thirty days.
- Whether push notifications get their own provider in the second release.
