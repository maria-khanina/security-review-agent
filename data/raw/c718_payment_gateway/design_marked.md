# Payment Gateway: Security Champion Notes

I collected the commitments of the gateway in one place.

## Context

Payments Edge Gateway, payments-core, payments-db (PostgreSQL), Acquirer connector, payment-events (Kafka).

## Commitments that we meet

1. ⟦S:REC-01|Balances are reconciled with the ledger every day, and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.⟧
3. ⟦S:IDM-01|Every operation that moves money takes an idempotency key, and a repeated request with the same key does not move the money again.⟧
4. ⟦S:VER-01|A replaced API version is kept for 12 months, and its removal is announced 90 days in advance.⟧
5. ⟦S:VER-02|Breaking changes of the API are released only as a new version of the API.⟧
8. ⟦S:JOB-01|Every scheduled job runs with its own service account, which cannot log in interactively.⟧
9. ⟦S:SUP-01|Support agents see card numbers and document numbers only in masked form.⟧

## Known deviations

- ⟦F1|Messages with personal data are copied to the log as well, so that support can follow a payment.⟧
- ⟦F2|The second approver of a limit change is the manager of the same agent, who signs without looking.⟧
