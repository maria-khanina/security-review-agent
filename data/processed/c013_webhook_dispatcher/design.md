# Webhook Dispatcher: Architecture and Security Control Catalogue

Author: Rina M., Security Champion, Integrations
Review: Security Architecture
Revision: 5 (revision 4 called the dispatcher "hook-sender"; the old name is retired but still appears in two dashboards)

## 1. Summary

The Webhook Dispatcher delivers platform events to the callback endpoints that merchants register. Merchants depend on it for payment and payout notifications, so its controls are catalogued here in detail. Reviewers should read the catalogue (section 5) first and the architecture afterwards.

## 2. Architecture

Platform services hand events to the dispatcher. The dispatcher queues deliveries on delivery-queue and delivers them to the Merchant callback endpoints, retrying failed attempts with growing delays. Merchants manage their subscriptions through an API exposed by the dispatcher.

There are five operations:

- POST /v1/subscriptions registers a callback endpoint (url, event_types, description) and returns id, url and status.
- GET /v1/subscriptions/{subscriptionId} returns a subscription.
- POST /v1/subscriptions/{subscriptionId}/rotate-secret rotates the subscription's secret (grace_period_hours) and returns the subscription.
- GET /v1/deliveries lists delivery attempts and can be filtered by status.
- POST /v1/deliveries/{deliveryId}/replay replays a delivery (reason) and returns it with the number of attempts.

The dispatcher is built and released through the shared platform pipeline like every other service of the integrations team. The dispatcher protects the integrity and confidentiality of the events it carries in line with the enterprise standards of the platform.

## 3. Delivery behavior

A delivery moves through queued, sent, delivered and failed. After a configured number of failed attempts the delivery is marked failed and the subscription is paused, with the reason visible in its status. A merchant can replay a failed delivery, which creates a new attempt and records the reason given. Events are delivered at least once, so merchants are expected to de-duplicate on the event identifier.

## 4. Subscription lifecycle

A subscription is active, paused or disabled. A merchant can pause and resume a subscription. The platform disables a subscription after a long run of failed deliveries and notifies the merchant. Secret rotation has a grace period during which the old and the new secret are both accepted.

## 5. Control catalogue

Control identifiers (W-1 and so on) match the compliance spreadsheet (link TBD; the older spreadsheet under the previous team name is stale).

### 5.1 Identity and access

- W-1: The API authenticates callers with JWT bearer tokens.
- W-3: Debug and administrative routes are not exposed to the internet.

### 5.2 Data protection

- W-4: Personal data is never placed in URLs.

### 5.3 Secrets and network

- W-6: Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.
- W-7: The approved secret manager is the only source of runtime secrets, fetched at start-up.

### 5.4 Logging

- W-9: Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.

### 5.5 Application security

- W-10: Requests from outside are checked against the schema and rejected if they do not conform.
- W-12: User input reaches the database only as query parameters, never as part of the query text.
- W-13: Only approved origins are permitted by the CORS configuration of the browser-facing API.

## 6. Capacity and operations

The dispatcher handles several thousand events per second at peak. It is stateless apart from the queue and runs as three replicas behind the internal load balancer (revision 4 said two). The queue is partitioned by subscription so that a slow merchant endpoint cannot hold up deliveries to others. Per-merchant concurrency is capped, and a circuit breaker pauses attempts to an endpoint that returns errors for a sustained period.

## 7. Observability

Delivery rate, failure rate and queue depth are shown on one dashboard per environment. An alert fires when the age of the oldest queued delivery exceeds a threshold defined in the runbook. Merchants can see their own delivery history through the API.

## 8. Open items

- Status column of the catalogue: the controls are listed without an implementation status; the spreadsheet carries the status (link TBD).
- The maximum number of subscriptions per merchant is not decided.
- The older design of the hook-sender (revision 1) lives in the archived wiki and may not open.
