# Refund Service: architecture in diagrams

## Context

```
[Merchant backend] --\
                      >--> [Refunds Gateway] --> [refund-core] --> [refund-db (PostgreSQL)]
[Support agents] ----/                               |
                                                     +--> [refund-events (Kafka)]
```

Caption: merchants and support agents enter through the Refunds Gateway, refund-core owns the refund state, refund-db keeps the records with the payment references, and every status change leaves as an event on refund-events.

## Lifecycle of a refund

```
requested --> approved --> executed
    |            |
    |            +--> failed
    +--> rejected
    +--> cancelled
```

Caption: `POST /v1/refunds` creates `requested` (payment_id, amount, currency, reason, requested_by), `POST /v1/refunds/{id}/approval` moves to `approved` or `rejected` (decision, comment), `POST /v1/refunds/{id}/cancellation` moves a pending refund to `cancelled` (reason). `GET /v1/refunds/{id}` and `GET /v1/refunds` read id, payment_id, status, amount, currency.

## Approval

```
requester --> refund-core --(amount > 1,000 EUR)--> second approver
```

Caption: ⟦S:PAY-02|Refunds and reversals above 1,000 EUR are approved by a second person, and the requester can never approve their own request.⟧ ⟦S:PAY-01|Every refund request carries an idempotency key, and a repeated key returns the first result without executing the refund again.⟧

## Amounts

```
[Refunds Gateway] --> [refund-core] --> [payment gateway]
                          |
                          +-- amount, currency
```

Caption: ⟦F2|refund-core reads the payment, books the refund and sends amount and currency on to the payment gateway.⟧

## Supporting documents

```
[Support agent] --file--> [refund-core] --> [object store]
```

Caption: an agent can attach a receipt or a customer letter to a request. ⟦S:UPL-01|Uploads are limited to 10 MB, and the type of a file is checked against an allowed list on its content, not on its name.⟧ ⟦S:UPL-02|Each uploaded file is scanned for malware before anyone else can open it.⟧

## Merchant data and reports

```
[Finance] --> [export call] --> [refund-core] --> [refund-db]
```

Caption: finance exports refunds per merchant. ⟦F1|Reports are generated for any merchant identifier that is passed to the export call.⟧ ⟦S:TEN-02|Merchant data in refund-db is separated by row-level security.⟧

⟦S:DR-02|Recovery of the service is required within 4 hours, which is demonstrated by an annual failover exercise.⟧

## Failure paths

```
payment gateway timeout (30 s) --> retry x5 (growing pause) --> failed --> ops queue
```

Caption: after the fifth retry the refund is `failed` and lands in the queue of the operations team (TBD owner of the queue).

## Rollout

```
phase 1: support agents only (1 month)  -->  phase 2: merchants in groups of 50  -->  switch-off of the monolith module
```

Caption: the monolith module stays one month after the last group (TBD date).
