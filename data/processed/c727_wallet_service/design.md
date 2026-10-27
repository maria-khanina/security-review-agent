# Wallet Service - What the Wiki Does Not Say

(tribal knowledge, written down once)

The wallet keeps balances and transactions. It runs behind the Mobile API Gateway, uses Keycloak for tokens and wallet-db (PostgreSQL) for data. The service is wallet-core.

Facts:

- Balances are reconciled with the ledger every day, and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.
- Differences found in a reconciliation are resolved within 5 working days.
- The daily outgoing transfers of a customer are limited by the limit table, and a change of a limit needs the approval of a second employee.
- Breaking changes of the API are released only as a new version of the API.
- The merchant sandbox contains only generated data and runs separately from production.
- Messages that cannot be processed go to a dead-letter queue, which is examined within one working day.
- Processed messages stay in the queue for months so that analysts can replay them.
- Every scheduled job runs with its own service account, which cannot log in interactively.
- Support agents see card numbers and document numbers only in masked form.
- A change of the phone number or the email address needs a one-time code that is sent to the old contact data.
