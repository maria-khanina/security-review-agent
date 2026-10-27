# Webhook Dispatcher

## Background and goals

The webhook dispatcher delivers event callbacks to the endpoints of merchants and retries when a delivery fails. Merchants register an endpoint once and then receive the events that they subscribed to: payment captured, refund paid, dispute opened.

## Components

- dispatcher (service)
- delivery-queue (message queue)
- merchant callback endpoints (third party)

## Interface

- POST /v1/subscriptions registers a callback endpoint
- GET /v1/subscriptions/{subscriptionId} retrieves a subscription
- POST /v1/subscriptions/{subscriptionId}/rotate-secret rotates the signing secret
- GET /v1/deliveries lists delivery attempts
- POST /v1/deliveries/{deliveryId}/retry retries a delivery by hand

## Delivery

An event is put on the delivery-queue per subscription. The dispatcher takes it from the queue and posts it to the endpoint. A 2xx answer ends the delivery. Anything else is retried after 1 minute, 5 minutes, 30 minutes, 2 hours and 12 hours; after that the delivery is marked `failed` and the merchant can retry it by hand.

## Commitments

- Callbacks to merchant endpoints are signed, and each carries a timestamp that the receiver can check against replay.
- Documents uploaded by customers are deleted within 30 days after the account is closed.
- Vulnerabilities rated critical are fixed in production within 7 days after they are published.
- Production data is not copied to test or development environments.
- Test accounts in production are removed within 7 days after the test ends.
- Messages to customers contain no card numbers, passwords or images of identity documents.
- The service register names an owner and a deputy.
- Alerts of severity high are acknowledged within 15 minutes.

## Open

- longer retry schedule for merchants in other time zones?
