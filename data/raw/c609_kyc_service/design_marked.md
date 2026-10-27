# KYC Service: Design Document

**Status:** draft for review  **Version:** 1.4

## 1. Scope

The KYC service collects the identity documents of customers, submits them to the verification vendor and stores the results. This document describes the components, the interface and the operational commitments of the service.

## 2. Components

| Component | Type | Purpose |
|---|---|---|
| kyc-orchestrator | service | case handling and calls to the vendor |
| kyc-documents | S3 bucket | uploaded documents |
| kyc-db | PostgreSQL | cases and results |
| Identity verification vendor | third party | document and face check |

## 3. Interface

- POST /v1/kyc/cases opens a verification case.
- POST /v1/kyc/cases/{caseId}/documents uploads an identity document.
- GET /v1/kyc/cases/{caseId} returns the status of the case.
- POST /v1/kyc/cases/{caseId}/submit submits the case to the verification vendor.
- GET /v1/kyc/cases lists the cases of a customer.

## 4. Case handling

A case has the states `open`, `submitted`, `verified`, `rejected` and `manual_review`. A case that is not answered by the vendor within 60 seconds remains `submitted`; the orchestrator asks again every 5 minutes for 24 hours and then moves the case to `manual_review`.

## 5. Compliance commitments


5.2 ⟦S:ARC-02|Documents uploaded by customers are deleted within 30 days after the account is closed.⟧

5.3 ⟦S:VUL-01|Vulnerabilities rated critical are fixed in production within 7 days after they are published.⟧


5.5 ⟦S:TST-01|Production data is not copied to test or development environments.⟧

5.6 ⟦S:TST-02|Test accounts in production are removed within 7 days after the test ends.⟧

5.7 ⟦S:EXP-01|Exported files that contain personal data are encrypted and are deleted from the download location after 7 days.⟧

5.8 ⟦S:EXP-02|Exports of more than 1,000 customer records require the written approval of the data owner.⟧

5.9 ⟦F1|The service register shows the name of the team for the KYC service; no person is named as the owner or the deputy.⟧

5.10 ⟦S:INV-02|The service register lists the personal data that the KYC service processes and the verification vendor as the third party that receives data from it.⟧

5.11 ⟦S:MON-01|Alerts of severity high are acknowledged within 15 minutes.⟧

5.12 ⟦S:WHK-01|Callbacks to customer endpoints are signed and carry a timestamp that the receiver can check against replay.⟧

## 6. Messages

⟦F2|Status messages by email show the full card number of the funding card so that customers recognise the account.⟧

## 7. Open points

- retention of rejected cases
- language of the vendor messages
