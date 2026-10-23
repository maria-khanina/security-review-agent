# Webhook Dispatcher - how it works (a design for people who join the team)

Written by Marek, Integrations team (junior engineer)
Reviewed by: Sofia

## 1. What is a webhook and why do we need it?

When something happens in our platform, for example a payment is paid or a payout is sent, a merchant often wants to know about it at once. The merchant could ask us every minute "is there something new?", but that is slow and it loads our servers. A webhook is the opposite: the merchant gives us an adress (an URL), and when the thing happens, we send a message to that adress. The Webhook Dispatcher is the service that keeps the adresses and sends the messages, and tries again when it does not work the first time.

## 2. The three pieces

1. **dispatcher.** The main service. It takes events from the other services of the platform, finds the merchants which want them, and sends the messages.
2. **delivery-queue.** A queue is like a line in a shop: the jobs wait in the line and are served one after one. Every message that must be sent is a job in this queue. I first thought a queue and a topic are the same, but my reviewer told me they are not; for the dispatcher we use a queue.
3. **Merchant callback endpoints.** The adresses of the merchants. They belong to the merchants, we only call them.

The way of one event is: a platform service gives the event to the dispatcher, the dispatcher puts a job for every interested merchant to delivery-queue, takes the job again from the queue and calls the merchant endpoint.

## 3. The API

The merchants manage their callbacks with five calls. All of them begin with /v1.

- **POST /v1/subscriptions** creates a subscription. The merchant sends url, event_types and description and receives id, url and status.
- **GET /v1/subscriptions/{subscriptionId}** shows one subscription.
- **POST /v1/subscriptions/{subscriptionId}/rotate-secret** makes a new secret for the subscription. The merchant sends grace_period_hours, which is the number of hours when the old secret still works. The answer is the subscription again.
- **GET /v1/deliveries** shows the delivery attempts, and it can be filtered by status. Every item has id, event_type, status and attempts.
- **POST /v1/deliveries/{deliveryId}/replay** sends a delivery once more. The merchant must write a reason, and the answer shows the delivery with the number of attempts.

## 4. What happens when something fails?

A delivery has the states queued, sent, delivered and failed. If the merchant does not answer or answers with an error, the dispatcher waits and tries again, and every time the waiting is longer. After many attempts the delivery becomes failed and the subscription is paused, so we do not waste time for a dead adress. The merchant can look at the failed deliveries and replay them. A replay is a new attempt, and the reason is saved, so later we can see why somebody did it.

When a request to the dispatcher cannot be processed, the dispatcher answers the caller with an HTTP status code. I did not write down which text is in the answer, because it is not decided yet.

Delivery is "at least once". It means that a merchant can receive the same event two times, for example when our dispatcher sent it but did not get the answer in time. Because of this the merchant must look at the event identifier and ignore the events he already has.

## 5. Security - my list

My reviewer asked me to write about security, so I collected what I know. I explain the words, because I had to learn them myself.

**Who is calling?** Authentication means to find out who the caller is. No external endpoint serves anonymous traffic; callers present an OAuth2 token or a TLS client certificate. Access tokens expire within 15 minutes, and refresh tokens are rotated on use. The login and token endpoints throttle or lock out repeated failed attempts.

**What may the caller do?** Authorization means to decide what the caller is allowed to do. Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it. A merchant can never see the deliveries of another merchant. Nothing administrative or meant for debugging can be called from outside our network.

**Secrets and keys.** A secret is a password or a key that gives access. Credentials are never committed to code, configuration, specifications or infrastructure-as-code files. The approved secret manager is the only source of runtime secrets, fetched at start-up. Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited. Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year. Outbound TLS connections always verify the peer certificate.

**Network.** delivery-queue and the databases sit in private subnets and are not publicly reachable. Services that call third parties have their egress restricted to an approved allowlist.

**Logs.** Logs are the diary of the service. The audit trail includes authentication failures, privilege changes and sensitive-data access.

**Test systems.** Non-production environments do not contain real personal or card data.

**Input and code.** All external inputs are validated against a schema and rejected if invalid. We use parameterized queries only, with no SQL built from user input by string concatenation. CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days. No container runs as root, and the root filesystem is read-only wherever possible.

**Two things we decided to do later.** Rate limiting is left for a later release, and there are no per-client limits at launch. The webhook payloads are sent unsigned, and the receivers trust the URL that they registered. The secret that rotate-secret changes is meant for the signature in a later version; at launch the message goes without it.

## 6. Subscription states

A subscription is active, paused or disabled. The merchant can pause and resume. The platform disables a subscription after a long series of failed deliveries and writes to the merchant. The merchant can repair the endpoint and enable the subscription again.

## 7. How we know it works

There is one dashboard for every environment with the number of messages in a second, the share of failed deliveries and the age of the oldest job in delivery-queue. An alert starts when the oldest job is older than the limit in the runbook. Merchants can see their own delivery history through the API.

## 8. Questions for the review

- How many subscriptions can one merchant have at most?
- Should a replay be limited to some number in an hour?
- Is it better to have one queue for all merchants or one for every big merchant?
