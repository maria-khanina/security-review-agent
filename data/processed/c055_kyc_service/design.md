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
- Key material is kept in KMS and separate from the data, and keys are rotated every year or sooner.
- Read access to the logging platform is granted per role: on-call engineers need it to find faults, security analysts need it to follow up alerts, and no other role is given access.
- The retention period is 24 months for customer records and 90 days for delivery logs, and expired data is removed by a scheduled deletion job.
- Every externally reachable API endpoint must authenticate callers with OAuth2/OIDC bearer tokens or mutual TLS.
- kyc-orchestrator reads its runtime configuration when it starts.
- kyc-db and brokers in private subnets, not publicly reachable.
- kyc-documents bucket blocks public access, private by default.

## data

- A register of personal fields with the purpose of each is kept for the service, and anything that is not in the register is not stored.
- Audit logs are written to tamper-evident storage with at least one year of retention.
- The vendor receives the customer id and the email only, as these are the fields its notification task needs, and a data processing agreement covers the transfer.
- External APIs must sit behind a WAF with rate limiting.
- Traffic between services, and from services to data stores, is encrypted in transit.
- Each export file is encrypted at rest, readable only by the authorized requester, and removed automatically after 72 hours.
- Logs carry opaque identifiers only and never include secrets, card numbers or personal data.
- Services inside the cluster trust each other because of the network they sit in, and internal calls carry no credentials.
- Backup encryption is on, and we test restoring from backup at least every six months.
- A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use.

## logs / api / ops

- Auth failures, privilege changes and sensitive data access are logged.
- Input validated against schema, invalid rejected.
- Parameterized queries only.
- Any authenticated caller can read any case or document if it knows the identifier.

## later

- manual review ui
- vendor retry policy
