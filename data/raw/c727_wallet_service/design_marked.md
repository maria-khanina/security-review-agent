# Wallet Service - What the Wiki Does Not Say

(tribal knowledge, written down once)

The wallet keeps balances and transactions. It runs behind the Mobile API Gateway, uses Keycloak for tokens and wallet-db (PostgreSQL) for data. The service is wallet-core.

Facts:

- ⟦S:REC-01|Balances are reconciled with the ledger every day, and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.⟧
- ⟦S:REC-02|Differences found in a reconciliation are resolved within 5 working days.⟧
- ⟦S:LIM-01|The daily outgoing transfers of a customer are limited by the limit table, and a change of a limit needs the approval of a second employee.⟧
- ⟦S:VER-02|Breaking changes of the API are released only as a new version of the API.⟧
- ⟦S:SBX-01|The merchant sandbox contains only generated data and runs separately from production.⟧
- ⟦S:MSG-01|Messages that cannot be processed go to a dead-letter queue, which is examined within one working day.⟧
- ⟦F1|Processed messages stay in the queue for months so that analysts can replay them.⟧
- ⟦S:JOB-01|Every scheduled job runs with its own service account, which cannot log in interactively.⟧
- ⟦S:SUP-01|Support agents see card numbers and document numbers only in masked form.⟧
- ⟦S:SUP-02|A change of the phone number or the email address needs a one-time code that is sent to the old contact data.⟧
