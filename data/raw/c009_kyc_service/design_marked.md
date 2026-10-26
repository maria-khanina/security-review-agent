# KYC service - design (v0.3, WIP)

## What

- kyc svc (kyc-orchestrator) recieves ID details + doc images from the customer app, keeps the images in S3 and the case in kyc-db (PostgreSQL), and sends the case to the ID verification vendor.
- ⟦F1|kyc-orchestrator is exposed to the customer app through the public API layer.⟧
- ⟦S:DATA-02|The retention period is 24 months for customer records and 90 days for delivery logs, and expired data is removed by a scheduled deletion job.⟧
- ⟦S:CRYPTO-04|Traffic between services, and from services to data stores, is encrypted in transit.⟧
- Endpoints: POST /v1/kyc/cases (open case), POST /v1/kyc/cases/{caseId}/documents (upload doc), GET /v1/kyc/cases/{caseId} (status), POST /v1/kyc/cases/{caseId}/submit (send to vendor), GET /v1/kyc/cases (list).

## Flow

1. app opens a case
2. app uploads doc images -> orchestrator -> ⟦F2|kyc-documents bucket (S3) holds the images⟧
3. app hits submit -> orchestrator sends name, DOB, country + images to vendor
4. vendor result goes back into kyc-db, status = verified / rejected / manual_review

## Data

- ⟦F4|We save every field that the customer app sends with the case, in case analytics wants it later.⟧
- ⟦S:DATA-03|Vendor gets only the fields above, under a signed DPA.⟧

## Security

- ⟦S:CRYPTO-03|TLS 1.2+ for all external traffic.⟧
- ⟦S:LOG-03|Audit logs must be tamper-evident and retained for at least one year.⟧
- ⟦S:CRYPTO-05|Approved algs only, no MD5, SHA-1, DES, 3DES or ECB.⟧
- ⟦S:AUTHZ-04|No admin or debug endpoints on the public side.⟧
- ⟦S:AUTHZ-05|Prod access reviewed quarterly.⟧
- ⟦S:LOG-02|Log lines are kept free of secrets, card numbers and personal details, and identifiers are opaque.⟧
- ⟦S:SECRET-01|No secrets in code, config, specs or infra definitions.⟧
- ⟦S:OPS-01|CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧
- ⟦S:SECRET-02|Runtime secrets must be fetched from the approved secret store at startup.⟧
- ⟦S:NET-01|kyc-db sits in private subnets, no public endpoint.⟧
- ⟦S:NET-02|S3 bucket: block public access, private by default.⟧
- ⟦S:API-01|All input validated against the schema, bad requests rejected with 400.⟧
- ⟦S:AUTH-02|Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.⟧
- ⟦S:API-05|Parameterized queries only.⟧

## Logging

- ⟦F3|Access to customer records is not recorded anywhere; the logs only show that the service started and stopped.⟧

## Open

- vendor sla for manual_review
- retry on vendor timeout
