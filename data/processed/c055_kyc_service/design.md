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
- No admin or debug endpoints on the public internet.
- Production access reviewed at least quarterly.
- kyc-orchestrator signs and protects the messages it exchanges with the vendor.
- External traffic TLS 1.2 or higher.
- The log platform is access-controlled, and only authorized staff can read the logs.
- Every externally reachable API endpoint must authenticate callers with OAuth2/OIDC bearer tokens or mutual TLS.
- kyc-orchestrator reads its runtime configuration when it starts.
- kyc-db and brokers in private subnets, not publicly reachable.
- kyc-documents bucket blocks public access, private by default.

## data

- Only the personal data needed for verification is collected and stored.
- Personal data to the vendor only under an approved DPA, only required fields.
- Each export file is encrypted at rest, readable only by the authorized requester, and removed automatically after 72 hours.
- Services inside the cluster trust each other because of the network they sit in, and internal calls carry no credentials.

## logs / api / ops

- Auth failures, privilege changes and sensitive data access are logged.
- Input validated against schema, invalid rejected.
- Parameterized queries only.
- Any authenticated caller can read any case or document if it knows the identifier.

## later

- manual review ui
- vendor retry policy
