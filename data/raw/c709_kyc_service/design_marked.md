# KYC Service - Notes from the Wiki (tribal edition)

You will not find all of this in the register, but here is how it works.

**What it is.** kyc-orchestrator (the service), kyc-documents (S3 bucket for the uploaded images), kyc-db (PostgreSQL) with the cases, and the identity verification vendor as the third party. The vendor checks the document and the face.

**Calls.** POST /v1/kyc/cases opens a case, POST /v1/kyc/cases/{caseId}/documents uploads, GET /v1/kyc/cases/{caseId} gives the status, POST /v1/kyc/cases/{caseId}/submit sends it to the vendor.

**Things everybody knows**
- ⟦S:LIM-01|The daily outgoing transfers of a customer are limited by the limit table, and a change of a limit needs the approval of a second employee.⟧
- ⟦S:SBX-01|The merchant sandbox has generated data only and runs apart from production.⟧
- ⟦S:MSG-01|Messages that cannot be processed go to the dead-letter queue, which is examined within one working day.⟧
- ⟦S:SUP-01|Support agents see card numbers and document numbers only masked.⟧

**Contact data.** ⟦F1|If a customer calls to change the phone number, the agent accepts the new number after the caller answers three questions.⟧
