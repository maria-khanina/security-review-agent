# KYC Service - Technical Design

## 1. About this document

This document describe the KYC Service of Meridian Pay. The service collect the identity data of new customers and the photo of their identity document, sends it to an external vendor for verification and keeps the result. The document is written for the engineers who will build and operate the service.

## 2. Components

- **kyc-orchestrator** is the main service. It has the whole logic of a case.
- **kyc-db (PostgreSQL)** keeps the cases and their status.
- **kyc-documents (S3)** keeps the images of the documents.
- **Identity verification vendor** is the external party that make the check.

The Customer app talks only to kyc-orchestrator. The orchestrator writes the case to kyc-db, the images to kyc-documents and sends the verification request to the vendor.

## 3. Interfaces

We have five calls.

1. **POST /v1/kyc/cases** open a case. In the request there are customer_id, full_name, date_of_birth and country. The answer has id, status, risk_level and customer_id.
2. **POST /v1/kyc/cases/{caseId}/documents** upload the image of the document. In the request there are document_type and content_base64. The answer has document_id and received_at.
3. **GET /v1/kyc/cases/{caseId}** give the case with id, status, risk_level and customer_id.
4. **POST /v1/kyc/cases/{caseId}/submit** send the case to the vendor. The request has the field consent, the answer has id, status, risk_level and customer_id.
5. **GET /v1/kyc/cases** give the list of cases, with the same four fields as the single case.

## 4. Where the data is stored

⟦S:RES-01|Personal data of customers in the EU is stored and processed only in regions of the EU.⟧ For this reason kyc-db and kyc-documents are created in one EU region and the vendor is connected over its EU endpoint.

For the work of the support team the operations team can make a snapshot of kyc-db. ⟦F1|The snapshots are shared with the analytics account of the data team, and nobody checks in which region this account keeps them.⟧

## 5. Delivery

The service is build and deployed by the pipeline of the platform team. ⟦S:PIP-01|The credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour.⟧ ⟦S:PIP-02|The build artifacts are signed, and the signature is verified before deployment.⟧

## 6. Change and rollback

Every change goes first to the pre-production environment. ⟦F2|The pre-production environment is very different from production: it has other database sizes, no vendor connection and a smaller number of replicas, so the team does not trust the result of a rollback test there and does not make such tests.⟧

## 7. Behaviour under load

⟦S:CAP-01|The public endpoints shed load with HTTP 503 instead of queueing requests when their capacity is exhausted.⟧ The mobile app show to the customer a message to try again after some minutes.

⟦S:PRV-03|The purposes of personal data are listed in the privacy notice that customers accept at sign-up, and the data is not used for any purpose outside that list.⟧

## 8. Failure handling

When the vendor does not answer in five minutes, the case get the status `needs_review` and an analyst takes it. When the upload of an image is not successful, the app get an error and the customer must send the image again. The failed image is not saved.

## 9. Rollout

The service starts with ten percent of the new customers. After two weeks without growth of the cases in `needs_review` all customers use it.
