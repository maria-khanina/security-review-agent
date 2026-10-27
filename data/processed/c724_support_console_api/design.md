support console api - slack paste

**what** support web console -> console-backend (service) -> console-db (PostgreSQL). Keycloak for login.

**endpoints** GET /v1/customers, GET /v1/customers/{customerId}, POST /v1/customers/{customerId}/second-factor-reset, POST /v1/customers/{customerId}/credits

**credits** up to 50 EUR alone, above that a second agent

**compliance stuff**
- Balances are reconciled with the ledger every day and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.
- Differences found in a reconciliation are resolved within 5 working days.
- Every operation that moves money takes an idempotency key, and a repeated request with the same key does not move the money again.
- A replaced API version is kept for 12 months and its removal is announced 90 days in advance.
- The merchant sandbox contains only generated data and runs separately from production.
- Messages that cannot be processed go to a dead-letter queue, which is examined within one working day.
- Messages with personal data are copied to the log as well, support needs them to follow a case.
- Every scheduled job runs with its own service account, which cannot log in interactively.
- Support agents see card numbers and document numbers only in masked form.
