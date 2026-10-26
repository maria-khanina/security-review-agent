# KYC Verification Service: Design

## Background and goals

The KYC Verification Service collects identity details and identity document images from customers, submits them to an external identity verification vendor and stores the verification result. It replaces the identity checks of the old onboarding platform (called "KYC Platform 1" in earlier documents and "the onboarding module" in the monolith). The goal is to shorten the time to open a verification case from days to minutes.

## Non-goals

- Sanctions screening is not part of this release.
- Ongoing monitoring of existing customers stays in the monolith.
- The customer web portal of the onboarding platform is not migrated; only the customer app is supported.

## Components

The Customer app calls kyc-orchestrator, the service described in this document (also called kyc-gateway in the old diagrams). kyc-orchestrator stores the case records in kyc-db (PostgreSQL) and the document images in the kyc-documents bucket (S3), and it sends the verification request to the Identity verification vendor. The vendor answers asynchronously, and kyc-orchestrator updates the case when the answer arrives.

## Endpoints

**POST /v1/kyc/cases** opens a verification case. The request carries customer_id, full_name, date_of_birth and country. The response returns id, status, risk_level and customer_id. A new case has the status `open` and the risk level `unknown`.

**POST /v1/kyc/cases/{caseId}/documents** uploads an identity document of the case. The request carries document_type and content_base64, and the response returns document_id and received_at. Supported document types are passport, national ID card and driving licence. Besides single images, the customer can upload a zip archive with all pages of the document, and kyc-orchestrator unpacks the archive and stores every file without a limit on the size of the archive or of its content. The document is passed to the malware scanner after it has been stored, and when the scanner is not reachable the failure is logged and the file is released anyway.

**GET /v1/kyc/cases/{caseId}** returns the case with id, status, risk_level and customer_id.

**POST /v1/kyc/cases/{caseId}/submit** submits the case to the vendor. The request carries the consent flag of the customer; without consent the case cannot be submitted. The response returns the same fields as the read call.

**GET /v1/kyc/cases** lists the cases of the customer with paging.

## The customer app

The customer app is the mobile app of Meridian Pay. The mobile app pins the public key of the Meridian Pay API and refuses every connection that fails the pinning check. The app keeps tokens and keys only in the secure storage of the operating system and never in preferences or in files. The app guides the customer through photographing the document, checks the sharpness of the picture and shows the status of the case.

We have set a recovery time objective of 4 hours or less, and every year we run a failover exercise to prove it.

A written runbook covers security incidents of the service, the on-call engineer can be paged around the clock, and a rehearsal takes place every six months.

## Third-party components

Every third-party SDK or library, including the SDK of the verification vendor, is approved before its first use, and the approved list is reviewed every six months.

## Data model

A case has an id, the customer id, the status (`open`, `submitted`, `approved`, `rejected`, `needs_review`), the risk level (`unknown`, `low`, `medium`, `high`), the timestamps of each change and the id of the vendor request. A document belongs to a case and has the type, the object key in the bucket and the time of receipt.

## Failure modes

When the vendor does not answer within five minutes, the case moves to `needs_review` and an analyst looks at it. When the upload of an image to the bucket fails, kyc-orchestrator tells the app to try again and keeps nothing of the failed upload.

## Rollout

The service goes live together with the app release 5.1. Ten percent of the new customers use it in the first week; if the share of cases in `needs_review` stays below five percent, all new customers follow in the second week. Existing open cases of KYC Platform 1 are finished there.

## Open questions

- How long the analysts get to review a case in `needs_review`.
- Whether the status `rejected` should carry a reason code in the first release.
