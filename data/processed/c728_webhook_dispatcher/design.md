# Webhook Dispatcher - Delta to Version 4

## What changes

1. A new retry step after 30 hours for merchants that ask for it.
2. `GET /v1/deliveries` can filter by status.
3. The delivery log shows the HTTP status of the last attempt.

## What stays

- dispatcher (service), delivery-queue (message queue), merchant callback endpoints (third party)
- Interface: `POST /v1/subscriptions`, `GET /v1/subscriptions/{subscriptionId}`, `POST /v1/subscriptions/{subscriptionId}/rotate-secret`, `GET /v1/deliveries`, `POST /v1/deliveries/{deliveryId}/retry`

## Commitments from version 4

- Every operation that moves money takes an idempotency key, and a repeated request with the same key does not move the money again.
- A replaced API version is kept for 12 months, and its removal is announced 90 days in advance.
- Breaking changes of the API are released only as a new version of the API.
- Messages that cannot be processed go to a dead-letter queue, which is examined within one working day.
- Messages are deleted from the queue after they are processed.
- Every scheduled job runs with its own service account, which cannot log in interactively.
