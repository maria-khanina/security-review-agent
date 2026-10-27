refund service - meeting notes (ticket review)

**people** Dana, Ruud, Sofie

**service** Refunds Gateway -> refund-core -> refund-db (PostgreSQL), events to refund-events (Kafka)

**api** POST /v1/refunds, GET /v1/refunds/{refundId}, GET /v1/refunds, POST /v1/refunds/{refundId}/approval, POST /v1/refunds/{refundId}/cancellation

**discussed**
- ⟦F3|The refund-core posts a daily summary of refunds to the finance channel.⟧
- ⟦S:REC-01|Balances are reconciled with the ledger every day and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.⟧
- ⟦F2|Idempotency keys are remembered for one minute.⟧
- ⟦S:VER-01|A replaced API version is kept 12 months, removal announced 90 days in advance.⟧
- ⟦S:SBX-01|Merchant sandbox: generated data only, runs separately from production.⟧
- ⟦S:MSG-01|Unprocessable messages go to the dead-letter queue, examined within one working day.⟧
- ⟦S:MSG-02|Processed messages are deleted from the queue.⟧
- ⟦S:JOB-01|Each scheduled job runs with its own service account that cannot log in interactively.⟧
- ⟦S:SUP-01|Agents see card numbers and document numbers only masked.⟧

**support** ⟦F1|When a customer changes the phone number, the code is sent to the new phone number, that is the quickest way to check it.⟧
