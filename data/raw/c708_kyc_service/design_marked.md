KYC service design (ESL)

The KYC service take identity documents from the customers, send them to the verification vendor and keep the result.

Parts
- kyc-orchestrator (service)
- kyc-documents (S3)
- kyc-db (PostgreSQL)
- Identity verification vendor (third party)

Endpoints
- POST /v1/kyc/cases - open a case
- POST /v1/kyc/cases/{caseId}/documents - upload a document
- GET /v1/kyc/cases/{caseId} - status
- POST /v1/kyc/cases/{caseId}/submit - send to the vendor

If the vendor not answer in 60 seconds the case stay `submitted` and the job ask again every 5 minutes for a day.

Rules
1. ⟦S:LIM-01|The daily outgoing transfers of a customer are limited by the limit table, and a change of a limit need the approval of a second employee.⟧
3. ⟦S:VER-02|Breaking changes of the API are released only as a new version of the API.⟧
5. ⟦S:MSG-01|Messages that cannot be processed go to a dead-letter queue, it is examined within one working day.⟧
6. ⟦S:MSG-02|Messages are deleted from the queue after they are processed.⟧
7. ⟦S:JOB-01|Every scheduled job run with its own service account, that cannot log in interactively.⟧

Support
- ⟦F2|The support agents see the full card number of the customer to find a payment faster.⟧
- ⟦F1|When a customer change the phone number or the email address, the change is made after a message to the old address, that the customer can ignore.⟧
