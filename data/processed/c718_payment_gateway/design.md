# Payment Gateway: Security Champion Notes

I collected the commitments of the gateway in one place.

## Context

Payments Edge Gateway, payments-core, payments-db (PostgreSQL), Acquirer connector, payment-events (Kafka).

## Commitments that we meet

1. Balances are reconciled with the ledger every day, and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.
3. Every operation that moves money takes an idempotency key, and a repeated request with the same key does not move the money again.
4. A replaced API version is kept for 12 months, and its removal is announced 90 days in advance.
5. Breaking changes of the API are released only as a new version of the API.
8. Every scheduled job runs with its own service account, which cannot log in interactively.
9. Support agents see card numbers and document numbers only in masked form.

## Known deviations

- Messages with personal data are copied to the log as well, so that support can follow a payment.
- The second approver of a limit change is the manager of the same agent, who signs without looking.
