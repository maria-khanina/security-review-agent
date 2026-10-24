# Webhook Dispatcher Design

## Part A (Priya, platform side)

### 1. Purpose

The Webhook Dispatcher delivers platform events to the callback endpoints that merchants register. Platform services hand events to the dispatcher, which queues them and delivers them with retries.

### 2. Components

- dispatcher: registers subscriptions, queues deliveries, performs delivery attempts.
- delivery-queue: holds pending deliveries.
- Merchant callback endpoints: the HTTPS endpoints of merchants.

### 3. API

- POST /v1/subscriptions registers a callback endpoint (url, event_types, description) and returns id, url and status.
- GET /v1/subscriptions/{subscriptionId} returns a subscription.
- POST /v1/subscriptions/{subscriptionId}/rotate-secret rotates the subscription's secret (grace_period_hours) and returns the subscription.
- GET /v1/deliveries lists delivery attempts, filterable by status.
- POST /v1/deliveries/{deliveryId}/replay replays a delivery (reason) and returns it with its attempts.

The dispatcher exposes the subscription and delivery calls to merchants through the public API host. All traffic is served over HTTPS only.

### 4. Security (platform controls)

- Nothing administrative or meant for debugging can be called from outside our network.
- Access to production is recertified at least once per quarter.
- Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.
- No secrets are kept in source code, config files, API specs or infrastructure definitions.
- Message brokers and databases sit in private subnets and are not publicly reachable.
- All external traffic must use TLS 1.2 or higher.
- The approved secret manager is the only source of runtime secrets, fetched at start-up.
- Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.

### 5. Deployment

The dispatcher runs as three replicas behind the internal load balancer. Rolling updates replace one replica at a time.

---

## Part B (Tom, service side)

#### deliveries

so the dispatcher (the worker in my notes, "hook sender" in the old proposal) takes an event, finds the subscriptions that listen to the event type, writes a delivery per subscription to delivery-queue and sends them. a failed attempt is retried with growing delays up to a limit, then the delivery is marked failed and shows up in GET /v1/deliveries. replay creates a new attempt for an existing delivery and needs a reason, which is stored. The dispatcher takes the filters of the delivery list and turns them into the lookups it needs.

The dispatcher runs as two replicas in our setup (the platform half says three, we need to align).

#### logging

- We log failed logins, changes of privileges and reads of sensitive data.

#### input and build

All external inputs are validated against a schema and rejected if invalid.

#### subscriptions

A subscription has an id, a url, a list of event types, a description and a status (active, paused, disabled). Disabling happens automatically after a long run of failed deliveries and the merchant sees the reason in the status. The secret rotation call has a grace period so that old and new secrets work side by side for a while.

##### Differences between the halves

Part A says three replicas, Part B says two. Part A says dispatcher, Part B says worker. The old proposal (link dead) called the queue "outbox".
