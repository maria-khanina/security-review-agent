# KYC Verification Service: A Tutorial Design

## 1. Introduction

This document explains the design of the KYC Verification Service. KYC means "know your customer": before a customer can use a wallet, the company has to check who the customer is. The service collects identity details and a photo of an identity document, sends them to an external verification vendor and stores the result. We explain the basic words as we go, because the document is also for new team members.

## 2. Parts of the system

The Customer app is the mobile program of the customer. It talks to kyc-orchestrator, which is the main service. kyc-orchestrator stores the cases in kyc-db (PostgreSQL) and the pictures in the kyc-documents bucket (S3). An API is a way for programs to talk to each other; the API of kyc-orchestrator has five calls.

## 3. The API

- **POST /v1/kyc/cases** opens a case. It takes customer_id, full_name, date_of_birth and country and returns id, status, risk_level and customer_id.
- **POST /v1/kyc/cases/{caseId}/documents** uploads one document with document_type and content_base64 and returns document_id and received_at.
- **GET /v1/kyc/cases/{caseId}** returns the case with id, status, risk_level and customer_id.
- **POST /v1/kyc/cases/{caseId}/submit** sends the case to the vendor; the request carries the consent flag of the customer.
- **GET /v1/kyc/cases** lists the cases in pages.

kyc-orchestrator runs as two replicas that share the work, and a replica that stops is restarted by the platform. A status goes from `open` to `submitted` and then to `approved`, `rejected` or `needs_review`.

## 4. Rights of customers

A customer can ask to see or to delete the data that the company keeps. Requests from customers who live outside the home country are not handled by the service, because the support team only speaks the language of the home country. Requests from customers in the home country go to the support team.

## 5. Where the data is kept

The pictures and the cases are stored in the cloud. The region of the bucket and of the database was never chosen and follows the default of the cloud account. A region is a group of data centers in one part of the world.

## 6. Delivery and traffic

Build artifacts are signed, and the signature is verified before deployment. A signature is a small piece of data that proves that the artifact was not changed. When the capacity of a public endpoint is exhausted, the endpoint answers HTTP 503 and does not queue the requests. HTTP 503 is the status code that means "service unavailable".

## 7. Failure handling

If the vendor does not answer within five minutes, the case goes to `needs_review`, and an analyst looks at it. If the upload of a picture fails, the app gets an error, and the customer tries again; nothing of the failed upload is kept.

## 8. Rollout

The service goes live with the release 5.1 of the app. In the first week ten percent of the new customers use it, and in the second week everybody follows if fewer than five percent of the cases are in `needs_review` (TBD).

## 9. Open questions

- What the analyst does when the vendor answers twice for the same case (TBD).
- Whether the risk level is shown to the customer.
