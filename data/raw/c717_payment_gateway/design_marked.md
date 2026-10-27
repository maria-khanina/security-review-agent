Payment Gateway - design in tables

| Item | Description |
|---|---|
| Entrance | Payments Edge Gateway |
| Core | payments-core (service) |
| Storage | payments-db (PostgreSQL) |
| Third party | Acquirer connector |
| Events | payment-events (Kafka) |

| Operation | Path |
|---|---|
| create | POST /v1/payments |
| retrieve | GET /v1/payments/{paymentId} |
| capture | POST /v1/payments/{paymentId}/capture |
| refund | POST /v1/payments/{paymentId}/refunds |
| list | GET /v1/payments |

| Topic | Commitment |
|---|---|
| Reconciliation | ⟦F2|Balances are compared with the ledger once a month, when finance closes the books.⟧ |
| Differences | ⟦S:REC-02|Differences found in a reconciliation are resolved within 5 working days.⟧ |
| Money operations | ⟦F1|Only the payment endpoint is idempotent; for refunds the caller has to make sure that it does not send twice.⟧ |
| Limits | ⟦S:LIM-01|The daily outgoing transfers of a customer are limited by the limit table, and a change of a limit needs the approval of a second employee.⟧ |
| API versions | ⟦S:VER-01|A replaced API version is kept for 12 months, and its removal is announced 90 days in advance.⟧ |
| Queues | ⟦S:MSG-01|Messages that cannot be processed go to a dead-letter queue, which is examined within one working day.⟧ ⟦S:MSG-02|Messages are deleted from the queue after they are processed.⟧ |
| Jobs | ⟦S:JOB-01|Every scheduled job runs with its own service account, which cannot log in interactively.⟧ |
| Support | ⟦S:SUP-02|A change of the phone number or the email address needs a one-time code that is sent to the old contact data.⟧ |
