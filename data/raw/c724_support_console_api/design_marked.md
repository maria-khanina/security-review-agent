support console api - slack paste

**what** support web console -> console-backend (service) -> console-db (PostgreSQL). Keycloak for login.

**endpoints** GET /v1/customers, GET /v1/customers/{customerId}, POST /v1/customers/{customerId}/second-factor-reset, POST /v1/customers/{customerId}/credits

**credits** up to 50 EUR alone, above that a second agent

**compliance stuff**
- ⟦S:REC-01|Balances are reconciled with the ledger every day and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.⟧
- ⟦S:REC-02|Differences found in a reconciliation are resolved within 5 working days.⟧
- ⟦S:IDM-01|Every operation that moves money takes an idempotency key, and a repeated request with the same key does not move the money again.⟧
- ⟦S:VER-01|A replaced API version is kept for 12 months and its removal is announced 90 days in advance.⟧
- ⟦S:SBX-01|The merchant sandbox contains only generated data and runs separately from production.⟧
- ⟦S:MSG-01|Messages that cannot be processed go to a dead-letter queue, which is examined within one working day.⟧
- ⟦F1|Messages with personal data are copied to the log as well, support needs them to follow a case.⟧
- ⟦S:JOB-01|Every scheduled job runs with its own service account, which cannot log in interactively.⟧
- ⟦S:SUP-01|Support agents see card numbers and document numbers only in masked form.⟧
