# refund service

## what
merchants and support agents request, approve, track refunds of card payments

## parts
- Refunds Gateway (public)
- refund-core
- ⟦F2|refund-db (PostgreSQL), refund records with payment refs and the card data of the payment.⟧
- ⟦S:CHG-01|Every change to production must be reviewed by a second engineer before it is deployed.⟧
- ⟦S:PRV-03|The service processes personal data only for the purposes listed in the privacy notice, and a new purpose is published to customers before the data is used.⟧
- refund-events (Kafka)

## endpoints
- POST /v1/refunds: payment_id, amount, currency, reason, requested_by -> id, payment_id, status, amount, currency
- GET /v1/refunds/{refundId} -> same 5 fields
- GET /v1/refunds -> same
- POST /v1/refunds/{refundId}/approval: decision, comment -> same
- POST /v1/refunds/{refundId}/cancellation: reason -> same

## data
- ⟦S:RES-02|backups and replicas of the personal data of customers in the EU stay in regions of the EU as well⟧
- ⟦S:OBS-02|Health check results and error rates are published to the shared dashboard every minute, and an alert fires when the error rate stays above 2% for five minutes.⟧
- retention of refund rows TBD

## delivery
- ⟦S:PIP-01|credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour⟧
- ⟦F1|only the images of the main service (refund-core) are signed, the other images are not⟧
- ⟦S:CHG-02|every change to production has a rollback plan that has been tested in a pre-production environment⟧

## load
- ⟦S:CAP-01|public endpoints answer HTTP 503 instead of queueing requests when their capacity is exhausted⟧

## events
- each transition -> event on refund-events after commit (outbox)

## rollout
- merchants pilot first, then all
- date TBD
