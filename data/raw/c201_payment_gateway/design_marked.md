# Payment GW v2

## Goal
- new payment service, replaces monolith payment module
- same 5 endpoints for merchants, no contract change
- status events to Kafka for ledger + notifications

## Parts
- Edge GW (a.k.a. PEG): entrance for merchant calls
- payments-core: state machine, talks to acquirer connector (acq-conn)
- ⟦F2|payments-db (PostgreSQL): payment + refund records of the merchants.⟧
- ⟦S:IR-02|A written runbook covers security incidents of the service, the on-call engineer can be paged around the clock, and a rehearsal takes place every six months.⟧
- payment-events topic

## Endpoints
- POST /v1/payments: amount, currency, card_token, merchant_id, reference -> id, status, amount, currency, last4, merchant_id
- GET /v1/payments/{id}: -> same fields
- POST /v1/payments/{id}/capture: amount (partial ok)
- POST /v1/payments/{id}/refunds: amount, reason -> id, status, amount
- GET /v1/payments: list, paging, newest first

## Idempotency
- ⟦S:PAY-01|Every payment operation (authorize, capture, refund, reversal) needs an idempotency key, and a repeated key returns the first result without running the operation again.⟧
- keys kept 24h, TBD check if enough for slow merchants

## Refunds
- full or partial, sum of refunds <= captured amount
- ⟦F1|Large refunds go to a manager for approval, and the money is paid out to the merchant first so the merchant is not waiting.⟧
- reason code mandatory (list TBD)

## Merchant data
- ⟦S:TEN-01|Every query on merchant data is filtered by the tenant id from the token, never by a request param.⟧
- reports per merchant: TBD

## Alerts
- ⟦F3|Alerts for failed logins and privilege changes are collected on the ops dashboard, whoever is on shift looks at it when something seems off.⟧

## Libs and recovery
- ⟦S:TPC-01|Third-party SDKs and libs need approval before first use; approved list reviewed every 6 months.⟧
- ⟦S:DR-01|payments-db: point-in-time recovery on, 7 days retention.⟧

## Failure
- acquirer timeout 3s -> payment stays pending, 5 retries -> then declined (acquirer_timeout)
- Kafka down -> outbox table in payments-db, relay job publishes later
- events can be late, not lost

## Rollout
- new merchants first, old ones in groups of ~50
- 1 week observation per group
- group goes back if declines +2 pts

## TBD
- list endpoint filter by status?
- partial capture event?
- who owns acq-conn on-call? TBD
