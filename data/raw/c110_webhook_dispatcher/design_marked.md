# Webhook Dispatcher: Vision and Roadmap

Owner: Integrations product team
Horizon: next four quarters

## 1. Why this matters

Merchants want to know what happens to their payments the moment it happens. The Webhook Dispatcher turns platform events into callbacks to the merchants' own systems, so that a merchant's shop, accounting tool or fulfilment system can react without polling us. Every integration we win or keep depends on callbacks that arrive reliably and in the right order of importance. This roadmap describes where the Dispatcher is today and where we want it to be at the end of the year.

## 2. Where we are today

Platform services hand events to the dispatcher. The dispatcher writes one delivery to delivery-queue per matching subscription and sends it to the Merchant callback endpoints, retrying failed attempts with growing delays. Merchants manage everything through five calls under /v1:

- POST /v1/subscriptions registers a callback endpoint (url, event_types, description) and returns id, url and status.
- GET /v1/subscriptions/{subscriptionId} returns a subscription.
- POST /v1/subscriptions/{subscriptionId}/rotate-secret rotates the secret of a subscription (grace_period_hours).
- GET /v1/deliveries lists delivery attempts, filterable by status, with id, event_type, status and attempts.
- POST /v1/deliveries/{deliveryId}/replay replays a delivery for a stated reason and returns it with the number of attempts.

Delivery is at least once. A subscription is active, paused or disabled, and the platform disables subscriptions after a long run of failed deliveries.

## 3. Controls in place today

These are the controls the Dispatcher runs with right now, listed so that the roadmap below is read against a clear starting point.

- ⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧
- ⟦S:AUTHZ-01|Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.⟧
- ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧
- ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
- ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧
- ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧
- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧
- ⟦S:API-01|All external inputs are validated against a schema and rejected if invalid.⟧
- ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧
- ⟦S:API-06|Browser-facing APIs allow only approved origins in CORS.⟧
- ⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧

## 4. Roadmap

**Q1: Fewer surprises for merchants.** A delivery log that merchants can filter by event type and by time, a clearer explanation of why a delivery failed, and a dashboard widget that shows the health of each subscription at a glance. Success is measured by the number of support tickets that begin with "I did not get my webhook", which we expect to halve.

**Q2: Faster recovery.** A bulk replay for all failed deliveries of a time window, replacing the one-by-one replay used today, and a pause button for a whole merchant. We also want to shorten the time between a merchant repairing an endpoint and the first successful delivery to under a minute.

**Q3: Smarter retries.** Retry schedules per event type, so that a payout confirmation is retried more aggressively than a marketing-style event, and a per-merchant concurrency view that shows which merchants are close to their cap.

**Q4: Self-service.** A merchant-facing page for managing subscriptions without calling the API, built on the same five operations, and a sandbox mode that lets a merchant send test events to an endpoint before going live.

## 5. Metrics

We track deliveries per second, the share of deliveries that succeed on the first attempt, the median time from event to successful delivery, and the number of subscriptions that are disabled by the platform each week. The target for the first-attempt success rate is 98 percent by the end of Q2 (TBD with the merchant success team, who want a separate target for the largest merchants).

## 6. Risks to the plan

The main risk is capacity: the queue is partitioned by subscription, and a few very large merchants produce most of the load. A second risk is that merchants build assumptions about ordering on top of a system that only guarantees at-least-once delivery, which the Q3 work on schedules must not make worse. The final risk is dependency on the integrations team's single on-call rota (TBD, owner: engineering manager).

## 7. Reference

The earlier "callback relay" concept note (link no longer available) contains the first estimate of event volumes. Numbers in it are outdated and should not be reused.
