# KYC service - design (v0.3, WIP)

## What

- kyc svc (kyc-orchestrator) recieves ID details + doc images from the customer app, keeps the images in S3 and the case in kyc-db (PostgreSQL), and sends the case to the ID verification vendor.
- ⟦F1|kyc-orchestrator is exposed to the customer app through the public API layer.⟧
- Endpoints: POST /v1/kyc/cases (open case), POST /v1/kyc/cases/{caseId}/documents (upload doc), GET /v1/kyc/cases/{caseId} (status), POST /v1/kyc/cases/{caseId}/submit (send to vendor), GET /v1/kyc/cases (list).

## Flow

1. app opens a case
2. app uploads doc images -> orchestrator -> ⟦F2|kyc-documents bucket (S3) holds the images⟧
3. app hits submit -> orchestrator sends name, DOB, country + images to vendor
4. vendor result goes back into kyc-db, status = verified / rejected / manual_review

## Data

- ⟦S:DATA-01|Collect only what KYC needs: full name, DOB, country, ID doc images. No extra profile fields.⟧
- ⟦S:DATA-03|Vendor gets only the fields above, under a signed DPA.⟧

## Security

- ⟦S:CRYPTO-03|TLS 1.2+ for all external traffic.⟧
- ⟦S:CRYPTO-05|Approved algs only, no MD5, SHA-1, DES, 3DES or ECB.⟧
- ⟦S:AUTHZ-04|No admin or debug endpoints on the public side.⟧
- ⟦S:AUTHZ-05|Prod access reviewed quarterly.⟧
- ⟦S:SECRET-01|No secrets in code, config, specs or infra definitions.⟧
- ⟦S:NET-01|kyc-db sits in private subnets, no public endpoint.⟧
- ⟦S:NET-02|S3 bucket: block public access, private by default.⟧
- ⟦S:API-01|All input validated against the schema, bad requests rejected with 400.⟧
- ⟦S:API-05|Parameterized queries only.⟧

## Logging

- ⟦S:LOG-01|Auth failures, privilege changes and access to sensitive data are logged.⟧

## Open

- vendor sla for manual_review
- retry on vendor timeout
