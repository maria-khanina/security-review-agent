# KYC Service - Technical Design

## 1. Goal

This document describe the KYC service of Meridian Pay. Service take identity data and photo of identity document from the customer, send it to external verification vendor and keep the result. We want that customer finish the verification in few minutes direct in the app, without visit in the branch.

## 2. Parts of the system

Customer app talk with kyc-orchestrator. The kyc-orchestrator is the heart of the system, it keep the cases in kyc-db (PostgreSQL) and the pictures in the bucket kyc-documents (S3). For the check of the person kyc-orchestrator call the Identity verification vendor and wait for the answer, the vendor answer later and not in the same request (TBD: how many minutes the vendor need in the worst case).

## 3. API

- POST /v1/kyc/cases: open new case. Request: customer_id, full_name, date_of_birth, country. Answer: id, status, risk_level, customer_id.
- POST /v1/kyc/cases/{caseId}/documents: upload one document. Request: document_type, content_base64. Answer: document_id, received_at.
- GET /v1/kyc/cases/{caseId}: status of the case, with id, status, risk_level and customer_id.
- POST /v1/kyc/cases/{caseId}/submit: send the case to the vendor, request has the flag consent.
- GET /v1/kyc/cases: list of the cases with paging.

Status of the case go from open to submitted, and then to approved, rejected or needs_review. Risk level is unknown until the vendor answer.

## 4. Mobile app

The app is available for iOS and Android. ⟦F1|For the connection to the API, the app trusts any certificate that the phone trusts, so we have no problem when the certificate of the gateway change.⟧ ⟦S:MOB-02|Tokens and keys are saved only in the secure storage of the operating system, and never in preferences or in files.⟧ The app check the sharpness of the photo before upload and show a hint if the picture is too dark.

## 5. Documents

The uploaded document is not open by any person or service before the check is finished. ⟦S:UPL-02|Every uploaded file is scanned for malware before any other user or service can open it.⟧ After the scan, the file stay in the bucket until the case is closed.

## 6. Operation

⟦S:IR-01|Alerts about repeated failed logins, privilege changes and access to card data reach the on-call engineer within 15 minutes.⟧ The on-call plan is in the wiki of the team (TBD link).

⟦S:TPC-01|Each third-party SDK or library is approved before the first use, and the list of approved components is reviewed every six months.⟧ This is valid also for the SDK of the vendor in the app.

## 7. Database

Database kyc-db keep the cases and the history of every status. ⟦F2|To save the cost of storage, the recovery of kyc-db keep the data of only one day, so we can go back not more than one day.⟧ The bucket kyc-documents has the versions of the objects switched on.

## 8. Failure and retry

If the vendor does not answer in five minutes the case go to needs_review and the analyst see it in the list. If the upload to the bucket fail, the app get the error and the customer must try again, nothing is saved from the failed try.

## 9. Rollout

The service start with the release 5.1 of the app. In the first week ten percent of new customers use it. If less than five percent of the cases is in needs_review, in the second week all new customers use it. The old cases stay in the old system until they are finished.

## 10. Open questions

- What the analyst must do when the answer of the vendor come twice for the same case.
- Should we show the risk level to the customer? Product say no, but it is not decided.
