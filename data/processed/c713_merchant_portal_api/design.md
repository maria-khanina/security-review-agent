Merchant Portal API: what we copied from the old doc and what we added

(1) The portal. Back office for merchants. Settlements, users, reports. portal-backend, portal-db, Portal Gateway, Keycloak, web app.

(2) Added in this version: report download links are shown in the list.

(3) Rules.
- Balances are reconciled with the ledger every day, and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.
- Differences found in a reconciliation are resolved within 5 working days.
- The daily outgoing transfers of a customer are limited by the limit table, and a change of a limit needs the approval of a second employee.
- Old API versions stay as long as somebody complains about their removal.
- Breaking changes of the API are released only as a new version of the API.
- The merchant sandbox contains only generated data and runs separately from production.
- Messages that cannot be processed go to a dead-letter queue, which is examined within one working day.
- Every scheduled job runs with its own service account, which cannot log in interactively.
- Support agents see card numbers and document numbers only in masked form.
