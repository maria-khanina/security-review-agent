Support Console API: diagram walkthrough

```
Support web console -> console-backend -> console-db (PostgreSQL)
                            |
                        Keycloak
```

The support agents use the web console. The console calls console-backend, which reads and writes console-db. Login goes through Keycloak. ⟦F3|The console-backend shows the agent the customer profile and the latest transactions of the customer.⟧

Endpoints: GET /v1/customers, GET /v1/customers/{customerId}, POST /v1/customers/{customerId}/second-factor-reset, POST /v1/customers/{customerId}/credits.

Commitments
- ⟦S:REC-02|Differences found in a reconciliation are resolved within 5 working days.⟧
- ⟦S:LIM-01|The daily outgoing transfers of a customer are limited by the limit table, and a change of a limit needs the approval of a second employee.⟧
- ⟦S:VER-01|A replaced API version is kept for 12 months, and its removal is announced 90 days in advance.⟧
- ⟦S:VER-02|Breaking changes of the API are released only as a new version of the API.⟧
- ⟦F1|The sandbox uses the production database server, in a separate schema.⟧
- ⟦S:MSG-01|Messages that cannot be processed go to a dead-letter queue, which is examined within one working day.⟧
- ⟦S:JOB-01|Every scheduled job runs with its own service account, which cannot log in interactively.⟧
- ⟦S:SUP-01|Support agents see card numbers and document numbers only in masked form.⟧
- ⟦F2|The one-time code for a change of the phone number or the email address is valid for a day and can be used many times.⟧
