# Ledger Service - Delta against Version 2

Only the changes are described here.

## Changed

1. Entries get a `source` field (payments, wallet, refunds, manual).
2. `GET /v1/entries` filters by `source`.
3. The reversal endpoint answers with the reversing entry.

## Unchanged and relevant

- ledger-core (service), ledger-db (PostgreSQL), ledger-events (Kafka)
- Balances are reconciled with the ledger every day, and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.
- Every operation that moves money takes an idempotency key, and a repeated request with the same key does not move the money again.
- A change of the error format is not treated as a breaking change and is made in the current version.
- The dead-letter queue of ledger-events exists, but nobody has looked at it since the launch.
- Messages in ledger-events are deleted after they are processed.
- Every scheduled job runs with its own service account, which cannot log in interactively.
- Support agents see card numbers and document numbers only in masked form.

## Rollout

Source field first, the filter one week later.
