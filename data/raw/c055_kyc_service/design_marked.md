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
- ⟦S:CRYPTO-06|Key material is kept in KMS and separate from the data, and keys are rotated every year or sooner.⟧
- ⟦S:LOG-04|Read access to the logging platform is granted per role: on-call engineers need it to find faults, security analysts need it to follow up alerts, and no other role is given access.⟧
- ⟦S:DATA-02|The retention period is 24 months for customer records and 90 days for delivery logs, and expired data is removed by a scheduled deletion job.⟧
- ⟦S:AUTH-01|Every externally reachable API endpoint must authenticate callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧
- ⟦F2|kyc-orchestrator reads its runtime configuration when it starts.⟧
- ⟦S:NET-01|kyc-db and brokers in private subnets, not publicly reachable.⟧
- ⟦S:NET-02|kyc-documents bucket blocks public access, private by default.⟧

## data

- ⟦S:DATA-01|A register of personal fields with the purpose of each is kept for the service, and anything that is not in the register is not stored.⟧
- ⟦S:LOG-03|Audit logs are written to tamper-evident storage with at least one year of retention.⟧
- ⟦S:DATA-03|The vendor receives the customer id and the email only, as these are the fields its notification task needs, and a data processing agreement covers the transfer.⟧
- ⟦S:NET-05|External APIs must sit behind a WAF with rate limiting.⟧
- ⟦S:CRYPTO-04|Traffic between services, and from services to data stores, is encrypted in transit.⟧
- ⟦S:DATA-05|Each export file is encrypted at rest, readable only by the authorized requester, and removed automatically after 72 hours.⟧
- ⟦S:LOG-02|Logs carry opaque identifiers only and never include secrets, card numbers or personal data.⟧
- ⟦F3|Services inside the cluster trust each other because of the network they sit in, and internal calls carry no credentials.⟧
- ⟦S:OPS-03|Backup encryption is on, and we test restoring from backup at least every six months.⟧
- ⟦S:AUTH-03|A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use.⟧

## logs / api / ops

- ⟦S:LOG-01|Auth failures, privilege changes and sensitive data access are logged.⟧
- ⟦S:API-01|Input validated against schema, invalid rejected.⟧
- ⟦S:API-05|Parameterized queries only.⟧
- ⟦F4|Any authenticated caller can read any case or document if it knows the identifier.⟧

## later

- manual review ui
- vendor retry policy
