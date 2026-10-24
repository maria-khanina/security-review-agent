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

- All state-changing operations require an authenticated caller.
- ⟦S:AUTHZ-04|No admin or debug endpoints on the public internet.⟧
- ⟦S:AUTHZ-05|Production access reviewed at least quarterly.⟧
- ⟦F1|kyc-orchestrator signs and protects the messages it exchanges with the vendor.⟧
- ⟦S:CRYPTO-03|External traffic TLS 1.2 or higher.⟧
- ⟦S:LOG-04|The log platform is access-controlled, and only authorized staff can read the logs.⟧
- ⟦S:AUTH-01|Every externally reachable API endpoint must authenticate callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧
- ⟦F2|kyc-orchestrator reads its runtime configuration when it starts.⟧
- ⟦S:NET-01|kyc-db and brokers in private subnets, not publicly reachable.⟧
- ⟦S:NET-02|kyc-documents bucket blocks public access, private by default.⟧

## data

- ⟦S:DATA-01|Only the personal data needed for verification is collected and stored.⟧
- ⟦S:DATA-03|Personal data to the vendor only under an approved DPA, only required fields.⟧
- ⟦S:DATA-05|Each export file is encrypted at rest, readable only by the authorized requester, and removed automatically after 72 hours.⟧
- ⟦F3|Services inside the cluster trust each other because of the network they sit in, and internal calls carry no credentials.⟧

## logs / api / ops

- ⟦S:LOG-01|Auth failures, privilege changes and sensitive data access are logged.⟧
- ⟦S:API-01|Input validated against schema, invalid rejected.⟧
- ⟦S:API-05|Parameterized queries only.⟧
- ⟦F4|Any authenticated caller can read any case or document if it knows the identifier.⟧

## later

- manual review ui
- vendor retry policy
