# Webhook Dispatcher: A Guided Design (for new joiners)

Author: Tobias, Integrations team (junior)
Reviewer: Hana

## 1. What problem does this solve?

When something happens in our platform, for example a payment succeeds, a merchant often wants to know immediately. Asking us again and again is wasteful, so instead the merchant gives us a web address, and when the event happens, we call that address and tell them. This is called a webhook, or a callback. The Webhook Dispatcher is the service that remembers the addresses and makes the calls reliably.

## 2. The pieces

- **dispatcher.** The service. It registers subscriptions, queues deliveries and makes the delivery attempts.
- **delivery-queue.** A queue is a line of waiting jobs. Each pending delivery stands in the line until the dispatcher takes it.
- **Merchant callback endpoints.** The addresses of the merchants that we call.

Platform services hand events to the dispatcher. The dispatcher writes a delivery to the queue for every merchant that subscribed to that kind of event, takes the deliveries from the queue and calls the merchant endpoints. I drew three boxes and three arrows to understand it.

## 3. The API

Merchants manage their callbacks through five calls.

- POST /v1/subscriptions registers an endpoint. The merchant sends a url, a list of event types and a description, and gets back an id, the url and a status.
- GET /v1/subscriptions/{subscriptionId} returns one subscription.
- POST /v1/subscriptions/{subscriptionId}/rotate-secret changes the secret of a subscription. A grace period in hours says how long the old secret keeps working next to the new one.
- GET /v1/deliveries lists delivery attempts and can be filtered by status.
- POST /v1/deliveries/{deliveryId}/replay tries a delivery again. The merchant must give a reason, and the reply shows the delivery with the number of attempts.

## 4. Who may call the API?

Authentication means finding out who is calling. All state-changing operations require an authenticated caller. Authorization means deciding what that caller may do. A merchant must never see the deliveries of another merchant. Administrative and debug endpoints are not reachable from the public internet.

Card numbers are never returned by the API. The event payloads only carry identifiers and amounts.

## 5. Traffic and limits

When I started I thought the dispatcher would need strict limits, but the team explained that our merchants are known partners. We expect partners to behave and therefore have no limits on request volume. If this causes problems, we will add limits later.

## 6. Cryptography

Encryption makes data unreadable without a key. Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.

## 7. Secrets and network

A secret is anything that gives access, like a password or a key. Secrets do not appear in source code, configuration files, specifications or infrastructure definitions. Runtime secrets are fetched from the approved secret store at startup.

## 8. Logs, input and code

Logs are the diary of the system. Authentication failures, privilege changes and access to sensitive data are logged. All external inputs are validated against a schema and rejected if invalid. Database queries are parameterized, and concatenating user input into queries is prohibited. Browser-facing APIs allow only approved origins in CORS.

## 9. Build

The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.

## 10. How a delivery lives

A delivery starts as queued. When the dispatcher calls the merchant and gets a success answer, it becomes delivered. If the merchant answers with an error or does not answer, the delivery goes back to the queue and is tried again later, with a longer wait each time. After a limit of attempts, the delivery becomes failed. The merchant sees failed deliveries in the list and can replay them. A replay creates a new attempt and stores the reason, so there is a history of why somebody tried again.

Events are delivered at least once. This means a merchant may receive the same event twice, so merchants should check the event identifier and ignore events they already handled. I wrote this in the merchant guide too (see the old guide, the link may not open).

## 11. Subscription states

A subscription is active, paused or disabled. A merchant can pause and resume a subscription. The platform disables a subscription after a long series of failed deliveries and tells the merchant, who can fix the endpoint and enable it again.

## 12. Questions for the review

- What is the maximum number of subscriptions per merchant?
- Should replays be limited per hour?
