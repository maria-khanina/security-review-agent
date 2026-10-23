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

AC-6. ⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧
AC-7. ⟦S:AUTHZ-01|Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.⟧
AC-8. ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧
AC-10. ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
AC-11. ⟦S:SECRET-01|Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.⟧
AC-12. ⟦S:SECRET-02|Runtime secrets are read from the secret store when the service starts.⟧
AC-14. ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are written to the logs.⟧
AC-15. ⟦S:API-01|Requests from outside are checked against the schema and rejected if they do not conform.⟧
AC-17. ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧
AC-18. ⟦S:API-06|Browser-facing APIs allow only approved origins in CORS.⟧
AC-19. ⟦S:OPS-01|Every build scans libraries and container images, and critical vulnerabilities get a 14-day fix deadline.⟧

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
