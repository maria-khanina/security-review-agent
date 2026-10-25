# refund service

## what
merchants and support agents request, approve, track refunds of card payments

## parts
- Refunds Gateway (public)
- refund-core
- refund-db (PostgreSQL), refund records with payment refs and the card data of the payment.
- refund-events (Kafka)

## endpoints
- POST /v1/refunds: payment_id, amount, currency, reason, requested_by -> id, payment_id, status, amount, currency
- GET /v1/refunds/{refundId} -> same 5 fields
- GET /v1/refunds -> same
- POST /v1/refunds/{refundId}/approval: decision, comment -> same
- POST /v1/refunds/{refundId}/cancellation: reason -> same

## data
- backups and replicas of the personal data of customers in the EU stay in regions of the EU as well
- retention of refund rows TBD

## delivery
- credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour
- only the images of the main service (refund-core) are signed, the other images are not
- every change to production has a rollback plan that has been tested in a pre-production environment

## load
- public endpoints answer HTTP 503 instead of queueing requests when their capacity is exhausted

## events
- each transition -> event on refund-events after commit (outbox)

## rollout
- merchants pilot first, then all
- date TBD
