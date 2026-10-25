# Webhook Dispatcher - Flow Diagram

```
 Platform services ──events──▶ dispatcher ──pending──▶ delivery-queue
                                  │
                                  └──signed payload──▶ Merchant callback endpoints
                                  ▲
                      merchants (REST: subscriptions, deliveries)
```

## Boxes

- **Platform services**: send the events that merchants subscribed to.
- **dispatcher**: stores subscriptions, creates the deliveries, signs the payload and sends it.
- **delivery-queue**: holds the pending deliveries and the retries.
- **Merchant callback endpoints**: the URLs of the merchants, outside of the platform.

## Calls

- POST /v1/subscriptions: url, event_types, description ▶ id, url, status. Registers a callback endpoint.
- GET /v1/subscriptions/{subscriptionId}: ▶ id, url, status.
- POST /v1/subscriptions/{subscriptionId}/rotate-secret: grace_period_hours ▶ id, url, status. The old secret stays valid during the grace period.
- GET /v1/deliveries: ▶ id, event_type, status, attempts.
- POST /v1/deliveries/{deliveryId}/replay: reason ▶ id, event_type, status, attempts.

## Arrows

- Platform services ▶ dispatcher: event with type and payload.
- dispatcher ▶ delivery-queue: delivery with attempt counter.
- dispatcher ▶ merchant endpoint: POST of the signed payload, HTTP 2xx means delivered.

## Retries

```
 attempt 1 ─fail─▶ +1 min ─▶ attempt 2 ─fail─▶ +5 min ─▶ attempt 3 ─fail─▶ +30 min ─▶ ... ─▶ attempt 8 ─fail─▶ status failed
```

## Capacity

The gateway in front of the dispatcher holds the requests for up to a minute when the dispatcher is slow, and answers when a worker is free.

## Delivery

```
 commit ▶ build ▶ sign ▶ verify ▶ deploy
```

Credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour. Build artifacts are signed, and the signature is verified before deployment. The dispatcher is released by the platform pipeline several times a week.

## Metrics

Boxes emit latency, queue depth and delivery success rate per merchant.
