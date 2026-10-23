# Webhook Dispatcher: Security Control Catalogue and Architecture

Author: Katya L., Security Champion, Integrations
Revision: 5 (revision 4 and the older "callback relay" page are still linked from the team wiki and are partly outdated)
Review: Security Architecture

## 1. Summary

The Webhook Dispatcher sends platform events to the callback addresses that merchants register. Merchants build payment and payout workflows on these events, so the dispatcher is a trust boundary: it holds merchant URLs and secrets and it calls systems that Meridian Pay does not control. This document describes the architecture first and then catalogues the security controls with identifiers that match the compliance tracker. The tracker, not this page, is the place that says whether a control is implemented; the catalogue only lists what the design commits to.

## 2. Architecture

Platform services hand events to the dispatcher. The dispatcher writes one delivery to delivery-queue for each matching subscription and later sends it to the Merchant callback endpoints. Failed deliveries are retried with growing delays. Merchants manage subscriptions and look at their deliveries through the dispatcher API.

The API has five operations, all under /v1:

- POST /v1/subscriptions registers a callback endpoint. The request has url, event_types and description; the response has id, url and status.
- GET /v1/subscriptions/{subscriptionId} returns a subscription.
- POST /v1/subscriptions/{subscriptionId}/rotate-secret rotates the secret of a subscription. The request has grace_period_hours; the response is the subscription.
- GET /v1/deliveries lists delivery attempts and can be filtered by status. Each item has id, event_type, status and attempts.
- POST /v1/deliveries/{deliveryId}/replay replays a delivery. The request has a reason; the response has id, event_type, status and attempts.

## 3. Delivery behavior

A delivery moves through queued, sent, delivered and failed. After a configured number of failed attempts the delivery becomes failed and the subscription is paused with the reason in its status. A replay creates a new attempt and stores the reason. Delivery is at least once, so merchants de-duplicate on the event identifier. The queue is partitioned by subscription so that a slow merchant endpoint cannot delay the others, and per-merchant concurrency is capped.

## 4. Subscription lifecycle

A subscription is active, paused or disabled. Merchants pause and resume their own subscriptions. The platform disables a subscription after a long run of failed deliveries and notifies the merchant. During secret rotation both secrets are accepted until the grace period ends. The old "callback relay" documentation described a manual rotation by e-mail; that process is gone (the page is still linked and may be misleading).

## 5. Control catalogue

Identifiers (D-1 and so on) match the compliance tracker (link to the tracker is not available from this page; the 2022 spreadsheet is stale).

### 5.1 Authentication and authorization

- D-1: ⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧
- D-2: ⟦F1|The dispatcher issues and accepts access tokens through the identity provider that the platform uses for all its external APIs.⟧
- D-3: ⟦S:AUTHZ-01|Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.⟧
- D-4: ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧
- D-5: ⟦S:AUTHZ-05|Access rights to production systems are reviewed at least quarterly.⟧

### 5.2 Transport and cryptography

- D-6: ⟦S:CRYPTO-03|All external traffic uses TLS 1.2 or higher.⟧
- D-7: ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧

### 5.3 Secrets and network

- D-8: ⟦F2|The credentials of the service are passed on the command line when the service starts.⟧
- D-9: ⟦S:NET-01|delivery-queue and the databases sit in private subnets and are not publicly reachable.⟧

### 5.4 Logging

- D-10: ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧

### 5.5 Application security

- D-11: ⟦F3|Requests are validated against strict schemas.⟧
- D-12: ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧

## 6. Deployment and capacity

The dispatcher is stateless apart from the queue. It runs as three replicas behind the internal load balancer (revision 4 said two). It handles several thousand events a second at the peak. A circuit breaker pauses attempts to an endpoint that has failed for a sustained period, and the pause is shown in the subscription status.

## 7. Observability

Delivery rate, failure rate and queue depth are shown on one dashboard per environment. An alert fires when the age of the oldest queued delivery passes the threshold in the runbook. Merchants see their own delivery history through the API. The on-call rota of the integrations team receives the alerts; the runbook lives in the integrations space (link to the old space may not open).

## 8. Known gaps in this document

The catalogue lists controls without their implementation status. The maximum number of subscriptions per merchant is not decided. The sections of revision 3 about the manual onboarding of merchants are kept in the archive and are not repeated here.
