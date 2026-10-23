# kyc svc - design (draft)

## flow

- customer app -> kyc-orchestrator: details + doc images
- orchestrator -> S3 bucket kyc-documents (images), kyc-db (case records)
- orchestrator -> verification vendor (verify request)
- vendor result back, case status updated

## api

- POST /v1/kyc/cases - open case (customer_id, full_name, date_of_birth, country)
- POST /v1/kyc/cases/{caseId}/documents - upload doc (document_type, content_base64)
- GET /v1/kyc/cases/{caseId} - status
- POST /v1/kyc/cases/{caseId}/submit - send to vendor (consent)
- GET /v1/kyc/cases - list

## states

opened > documents_received > submitted > verified / rejected / manual_review

## security

- ⟦F3|All state-changing operations require an authenticated caller.⟧
- ⟦S:AUTHZ-04|No admin or debug endpoints on the public internet.⟧
- ⟦S:AUTHZ-05|Production access reviewed at least quarterly.⟧
- ⟦F1|kyc-orchestrator signs and protects the messages it exchanges with the vendor.⟧
- ⟦S:CRYPTO-03|External traffic TLS 1.2 or higher.⟧
- ⟦F2|kyc-orchestrator reads its runtime configuration when it starts.⟧
- ⟦S:NET-01|kyc-db and brokers in private subnets, not publicly reachable.⟧
- ⟦S:NET-02|kyc-documents bucket blocks public access, private by default.⟧

## data

- ⟦S:DATA-01|Only the personal data needed for verification is collected and stored.⟧
- ⟦S:DATA-03|Personal data to the vendor only under an approved DPA, only required fields.⟧
- ⟦S:DATA-05|Exports with personal data need authorization, are encrypted in storage and expire.⟧

## logs / api / ops

- ⟦S:LOG-01|Auth failures, privilege changes and sensitive data access are logged.⟧
- ⟦S:API-01|Input validated against schema, invalid rejected.⟧
- ⟦S:API-05|Parameterized queries only.⟧

## later

- manual review ui
- vendor retry policy
