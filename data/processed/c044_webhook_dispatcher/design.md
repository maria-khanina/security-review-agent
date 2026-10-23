# Webhook Dispatcher: Architecture and Security Control Catalogue

Author: Rina M., Security Champion, Integrations
Review: Security Architecture
Revision: 6 (revision 5 called the dispatcher "hook-sender"; the old name is retired but still appears in two dashboards)

## 1. Summary

The Webhook Dispatcher delivers platform events to the callback endpoints that merchants register. Merchants rely on it for payment and payout notifications, so its controls are catalogued here in detail. Reviewers should read the catalogue (section 5) first and the architecture afterwards.

## 2. Architecture

Platform services hand events to the dispatcher. The dispatcher writes a delivery to delivery-queue for every matching subscription and delivers it to the Merchant callback endpoints, retrying failed attempts with growing delays. Merchants manage subscriptions through the dispatcher's API.

There are five operations:

- POST /v1/subscriptions registers a callback endpoint (url, event_types, description) and returns id, url and status.
- GET /v1/subscriptions/{subscriptionId} returns a subscription.
- POST /v1/subscriptions/{subscriptionId}/rotate-secret rotates the subscription's secret (grace_period_hours) and returns the subscription.
- GET /v1/deliveries lists delivery attempts and can be filtered by status.
- POST /v1/deliveries/{deliveryId}/replay replays a delivery (reason) and returns it with the number of attempts.

## 3. Delivery behavior

A delivery moves through queued, sent, delivered and failed. After a configured number of failed attempts the delivery is marked failed and the subscription is paused, with the reason in its status. A replay creates a new attempt and records the reason. Delivery is at least once; merchants de-duplicate on the event identifier.

## 4. Subscriptions

A subscription is active, paused or disabled. Merchants can pause and resume. The platform disables a subscription after a long run of failed deliveries and notifies the merchant. Secret rotation has a grace period in which both secrets are accepted.

## 5. Control catalogue

Control identifiers (W-1 and so on) match the compliance spreadsheet (link TBD; the older spreadsheet under the previous team name is stale and may not open).

### 5.1 Identity and access

- W-1: Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.
- W-2: Access tokens expire within 15 minutes, and refresh tokens are rotated on use.
- W-3: The login and token endpoints throttle or lock out repeated failed attempts.
- W-4: Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.
- W-5: Administrative and debug endpoints are not reachable from the public internet.

### 5.2 Cryptography and transport

- W-7: Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- W-8: Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.
- W-9: Services validate TLS certificates and never disable verification.

### 5.3 Secrets and network

- W-10: Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- W-11: Runtime secrets are fetched from the approved secret store at startup.
- W-13: delivery-queue and the databases sit in private subnets and are not publicly reachable.
- W-14: Services that call third parties have their egress restricted to an approved allowlist.

### 5.4 Logging and data

- W-15: Authentication failures, privilege changes and access to sensitive data are logged.
- W-17: Non-production environments do not contain real personal or card data.

### 5.5 Application security

- W-18: All external inputs are validated against a schema and rejected if invalid.
- W-20: Webhook payloads, outbound and inbound, are signed and the signatures are verified.
- W-21: Error responses do not reveal stack traces, SQL or internal hostnames.
- W-22: Database queries are parameterized, and concatenating user input into queries is prohibited.

### 5.6 Operations

- W-23: The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.
- W-24: Containers run as a non-root user, with a read-only root filesystem where possible.

## 6. Capacity and deployment

The dispatcher handles several thousand events per second at peak. It is stateless apart from the queue and runs as three replicas behind the internal load balancer (revision 5 said two). The queue is partitioned by subscription so that a slow merchant endpoint cannot hold up deliveries to others. Per-merchant concurrency is capped, and a circuit breaker pauses attempts to an endpoint that errors for a sustained period.

## 7. Observability

Delivery rate, failure rate and queue depth are shown on one dashboard per environment. An alert fires when the age of the oldest queued delivery exceeds a threshold defined in the runbook. Merchants can see their own delivery history through the API.

## 8. Open items

- Status column of the catalogue: controls are listed without an implementation status; the spreadsheet carries it (link TBD).
- The maximum number of subscriptions per merchant is not decided.
- Reference to revision 1 of the design lives in the archived wiki and may not open; the older Integrations space (link) is also stale.
