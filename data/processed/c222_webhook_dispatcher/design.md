# HOOK-120: Webhook Dispatcher

**Type:** Epic  **Priority:** Medium  **Component:** webhooks  **Reporter:** Platform Integrations

## Description

The Webhook Dispatcher delivers events of the platform to the callback endpoints of the merchants. Merchants register a subscription with a callback URL and the event types they want, and the dispatcher delivers every matching event, retries failed deliveries and lets the merchant replay a delivery. Platform services hand their events to the dispatcher through the delivery queue.

## User stories

**HOOK-121** As a merchant, I want to register a subscription so that I receive the events I need.
Acceptance criteria:
1. POST /v1/subscriptions accepts url, event_types and description.
2. The response contains id, url and status.
3. A new subscription is active after the first successful test delivery.

**HOOK-122** As a merchant, I want to read my subscription so that I can check its status.
Acceptance criteria:
1. GET /v1/subscriptions/{subscriptionId} returns id, url and status.

**HOOK-123** As a merchant, I want to rotate the secret of my subscription so that I can replace it without losing events.
Acceptance criteria:
1. POST /v1/subscriptions/{subscriptionId}/rotate-secret accepts grace_period_hours.
2. During the grace period both the old and the new secret are valid.
3. The response contains id, url and status.

**HOOK-124** As a merchant, I want to see my deliveries so that I know what was sent.
Acceptance criteria:
1. GET /v1/deliveries returns id, event_type, status and attempts, in pages.
2. The list is filtered by the merchant in the handlers of the subscriptions, and the handler of the deliveries relies on the caller to pass the right merchant.

**HOOK-125** As a merchant, I want to replay a delivery so that I can recover from a failure on my side.
Acceptance criteria:
1. POST /v1/deliveries/{deliveryId}/replay accepts a reason.
2. The response contains id, event_type, status and attempts.
3. A replayed delivery is marked as a replay in its header.

## Delivery behavior

**HOOK-130** The dispatcher takes events from the delivery queue and sends them to the callback URL in order per subscription. A delivery that gets no success answer within ten seconds is retried after one minute, ten minutes and one hour, and then marked `failed`. The dispatcher runs as two instances behind the internal load balancer and is deployed by the platform team in rolling steps.

## Non-functional requirements

**HOOK-140** Alerting.
Acceptance criteria:
1. Alerts about repeated failed logins, privilege changes and access to card data reach the on-call engineer within 15 minutes.

## Rollout

HOOK-150: the dispatcher replaces the notification code of the monolith. Merchants move in groups; the group of the largest merchants moves last (see HOOK-099 for the migration list).
