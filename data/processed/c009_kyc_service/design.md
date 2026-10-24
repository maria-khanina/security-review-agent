# KYC service - design (v0.3, WIP)

## What

- kyc svc (kyc-orchestrator) recieves ID details + doc images from the customer app, keeps the images in S3 and the case in kyc-db (PostgreSQL), and sends the case to the ID verification vendor.
- kyc-orchestrator is exposed to the customer app through the public API layer.
- Endpoints: POST /v1/kyc/cases (open case), POST /v1/kyc/cases/{caseId}/documents (upload doc), GET /v1/kyc/cases/{caseId} (status), POST /v1/kyc/cases/{caseId}/submit (send to vendor), GET /v1/kyc/cases (list).

## Flow

1. app opens a case
2. app uploads doc images -> orchestrator -> kyc-documents bucket (S3) holds the images
3. app hits submit -> orchestrator sends name, DOB, country + images to vendor
4. vendor result goes back into kyc-db, status = verified / rejected / manual_review

## Data

- We save every field that the customer app sends with the case, in case analytics wants it later.
- Vendor gets only the fields above, under a signed DPA.

## Security

- TLS 1.2+ for all external traffic.
- Approved algs only, no MD5, SHA-1, DES, 3DES or ECB.
- No admin or debug endpoints on the public side.
- Prod access reviewed quarterly.
- No secrets in code, config, specs or infra definitions.
- Runtime secrets must be fetched from the approved secret store at startup.
- kyc-db sits in private subnets, no public endpoint.
- S3 bucket: block public access, private by default.
- All input validated against the schema, bad requests rejected with 400.
- Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.
- Parameterized queries only.

## Logging

- Access to customer records is not recorded anywhere; the logs only show that the service started and stopped.

## Open

- vendor sla for manual_review
- retry on vendor timeout
