# Webhook dispatcher: migration delta

This note lists only what changes relative to the old callback sender (called hook-sender in older tickets). Anything not listed behaves as before. The old design is no longer maintained.

## What changes

1. **Packaging.** The callback sender was a library inside the payments monolith; the dispatcher is a standalone service with its own deployment.
2. **Queueing.** Deliveries used to be sent inline during the request that produced the event. They are now written to delivery-queue and sent by the dispatcher, with retries and growing delays.
3. **Subscriptions.** Merchants used to register callback endpoints through support. They now register them through the API below.
4. **Visibility.** Merchants can list delivery attempts and replay a failed delivery themselves.

## What does not change

The event types, the payload shapes and the at-least-once delivery guarantee are unchanged. Merchants still de-duplicate on the event identifier.

## API

- POST /v1/subscriptions registers a callback endpoint (url, event_types, description) and returns id, url and status.
- GET /v1/subscriptions/{subscriptionId} returns a subscription.
- POST /v1/subscriptions/{subscriptionId}/rotate-secret rotates the subscription's secret (grace_period_hours) and returns the subscription.
- GET /v1/deliveries lists delivery attempts and can be filtered by status.
- POST /v1/deliveries/{deliveryId}/replay replays a delivery (reason) and returns it with its attempts.

## Delivery behavior

A delivery moves through queued, sent, delivered and failed. After a configured number of failed attempts the delivery is marked failed and the subscription is paused with the reason visible in its status. A replay creates a new attempt and stores the reason given. The old sender retried three times; the dispatcher keeps retrying with growing delays up to a limit.

## Security delta

Most properties are inherited from the old sender and are not repeated here. The points below changed shape with the standalone service:

- Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.
- Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.
- Administrative and debug endpoints are not reachable from the public internet.
- We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.
- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- Runtime secrets are read from the secret store when the service starts.
- Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.
- External inputs are accepted only if they validate against the schema.
- Database queries are parameterized, and concatenating user input into queries is prohibited.
- Cross-origin access is restricted to approved origins, and there is no wildcard.
- The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.

## Cutover

Cutover happens per merchant segment. A segment is first run in dual mode: the old sender still delivers and the dispatcher records what it would have delivered, and the two are compared for a week. After a clean week the old sender is switched off for that segment. The old runbook still lists a manual resend procedure through support; it is obsolete and will be removed.

## Open items

- Maximum number of subscriptions per merchant.
- Decommission date of the old library.
