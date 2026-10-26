# KYC service design meeting, notes

Attendees: Priya, Tomas, Lena, Ahmed (backend), Sofia (app)

## Decisions

- One service for the whole identity check, called kyc-orchestrator. It owns the case records in kyc-db (PostgreSQL) and the images in the kyc-documents bucket (S3).
- ⟦F1|kyc-orchestrator runs as two replicas and Ahmed's team deploys it with the same pipeline as the other services.⟧
- Five endpoints, same shape as in the draft: open a case (customer_id, full_name, date_of_birth, country), upload a document (document_type, content_base64), read a case, submit a case with the consent flag, list cases.
- The vendor answers asynchronously. The case moves from open to submitted, and then to approved, rejected or needs_review.
- If the vendor does not answer within five minutes the case goes to needs_review. (Tomas wanted ten minutes, we kept five.)
- Risk level is shown only to the analysts, not to the customer. Decided. Hmm, Lena says product may want to show it, reopen if they ask.

## Mobile app (Sofia)

- The app guides the customer to photograph the document and checks the sharpness before the upload.
- ⟦F2|Session tokens are cached in a file in the app directory, so the app starts faster after the customer comes back.⟧
- Sofia will check how large the pictures are on older phones. TBD.

## Documents

- ⟦S:UPL-02|Uploaded files are scanned for malware before any other user or service can open them.⟧ Decided with Ahmed, the scan runs in the same step as the storing, the file is invisible until the scan is done.
- Files stay in the bucket until the case is closed. (Earlier we said 30 days, Priya says case closing is cleaner. Keep case closing.)

## Operations

- ⟦S:TPC-01|Every third-party SDK or library needs approval before its first use, and the approved list is reviewed every six months.⟧ This includes the SDK of the verification vendor.
- ⟦S:DR-01|kyc-db has point-in-time recovery enabled, with seven days of retention.⟧
- ⟦S:DR-02|The recovery time objective of the service is 4 hours at most, and a failover exercise proves it at least once a year.⟧
- ⟦S:IR-02|For security incidents we keep a runbook for this service and a paged on-call owner, and we rehearse the runbook at least twice a year.⟧

## Rollout

- Release 5.1 of the app switches to the service. 10% of new customers in week one, everybody in week two if needs_review stays under 5%.
- Old open cases finish in the old system.

## Open questions

- How long do the analysts have for a case in needs_review? Nobody knows yet.
- What do we do when the vendor sends the same answer twice? Ahmed will propose something next week.
- Format of the reference number the customer sees in the app. TBD with design.
