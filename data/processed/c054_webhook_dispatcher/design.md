WHD-210: Webhook Dispatcher, delivery of platform events to merchant callbacks

Type: Story
Priority: High
Component: Integrations
Reporter: product
Assignee: integrations team

DESCRIPTION

As a merchant, I want to register a callback endpoint and receive the events that happen to my payments, so that my systems stay in sync without polling.

SCOPE

Components: dispatcher, delivery-queue, Merchant callback endpoints.

Flow: Platform services hand events to the dispatcher. The dispatcher puts a delivery on delivery-queue for each matching subscription and delivers it to the Merchant callback endpoints.

API (all under /v1):

- POST /v1/subscriptions: register a callback endpoint. Request: url, event_types, description. Response: id, url, status.
- GET /v1/subscriptions/{subscriptionId}: retrieve a subscription. Response: id, url, status.
- POST /v1/subscriptions/{subscriptionId}/rotate-secret: rotate the signing secret. Request: grace_period_hours. Response: id, url, status.
- GET /v1/deliveries: list delivery attempts, filterable by status. Response items: id, event_type, status, attempts.
- POST /v1/deliveries/{deliveryId}/replay: replay a delivery. Request: reason. Response: id, event_type, status, attempts.

ACCEPTANCE CRITERIA

Functional

AC-1. A registered subscription receives every event of the types it listed, at least once.
AC-2. A failed delivery is retried with increasing delay and ends in status failed after the configured number of attempts.
AC-3. A replay creates a new attempt and stores the reason.
AC-4. A subscription can be active, paused or disabled; merchants can pause and resume.
AC-5. During secret rotation both secrets are accepted until the grace period ends.

Security

AC-6. Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.
AC-7. Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.

Workloads are non-root, and read-only root filesystems are used wherever they can be.
AC-8. Administrative and debug endpoints are not reachable from the public internet.
AC-10. Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
AC-11. Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.
AC-12. Runtime secrets are read from the secret store when the service starts.

Public API traffic passes through a web application firewall with rate limits.

Nothing travels unencrypted inside our network, because service-to-service and service-to-datastore links are encrypted.
AC-14. Authentication failures, privilege changes and access to sensitive data are written to the logs.

We do not trust the internal network by itself: every internal call is authenticated with mTLS or workload identity tokens.
AC-15. Requests from outside are checked against the schema and rejected if they do not conform.
AC-17. Dynamic queries for the delivery list are assembled with string formatting, because the ORM is too slow.
AC-18. CORS is set to allow all origins, to unblock the frontend team.
AC-19. Every build scans libraries and container images, and critical vulnerabilities get a 14-day fix deadline.

DEFINITION OF DONE

- All acceptance criteria verified in staging.
- Dashboards for delivery rate, failure rate and queue depth exist for each environment.
- Runbook entry for a stuck queue.
- Merchant guide updated with the at-least-once delivery note: merchants must de-duplicate on the event id.

OUT OF SCOPE

- Event schema design (WHD-198).
- Per-merchant retry policy overrides (WHD-215).
- Delivery history export (WHD-220).

NOTES

Delivery is at least once. The queue is partitioned by subscription so that one slow merchant endpoint does not delay the others.
