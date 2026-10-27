refund service - meeting notes (ticket review)

**people** Dana, Ruud, Sofie

**service** Refunds Gateway -> refund-core -> refund-db (PostgreSQL), events to refund-events (Kafka)

**api** POST /v1/refunds, GET /v1/refunds/{refundId}, GET /v1/refunds, POST /v1/refunds/{refundId}/approval, POST /v1/refunds/{refundId}/cancellation

**discussed**
- The refund-core posts a daily summary of refunds to the finance channel.
- Balances are reconciled with the ledger every day and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.
- Idempotency keys are remembered for one minute.
- A replaced API version is kept 12 months, removal announced 90 days in advance.
- Merchant sandbox: generated data only, runs separately from production.
- Unprocessable messages go to the dead-letter queue, examined within one working day.
- Processed messages are deleted from the queue.
- Each scheduled job runs with its own service account that cannot log in interactively.
- Agents see card numbers and document numbers only masked.

**support** When a customer changes the phone number, the code is sent to the new phone number, that is the quickest way to check it.
