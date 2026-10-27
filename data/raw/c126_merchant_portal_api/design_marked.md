merchant portal api - handover bullets (Dmitry)

what it is
- portal-backend: API behind the Portal Gateway for the Merchant web app: settlements, merchant users, reports
- portal-db (PostgreSQL): settlements, users, report jobs
- Keycloak: merchant user sign-in (OIDC), gateway validates tokens against it

endpoints (all /v1)
- GET /settlements (list, filter by status), GET /settlements/{settlementId} -> id, period, gross, fees, net
- POST /users (invite: email, role) -> id, email, role
- PATCH /users/{userId}/role (role) -> id, email, role
- POST /reports (report_type, from_date, to_date) -> id, status, expires_at
- GET /reports/{reportId}/download -> id, status, expires_at

how things behave
- reports are built async by a worker, status goes pending -> ready
- settlements are read-only, come from the settlement batch at 04:00
- invite sends a mail with a link, role defaults to viewer

access (usual platform setup applies, rest in the platform handbook)
- ⟦S:AUTH-01|Every request to an externally reachable endpoint is authenticated, either with an OIDC bearer token or with a mutual TLS client certificate.⟧
- ⟦F1|The second factor is optional for administrators, and most of them have not enabled it.⟧
- ⟦S:AUTHZ-01|Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.⟧
- ⟦S:NET-05|Public API traffic passes through a web application firewall with rate limits.⟧
- ⟦S:AUTHZ-04|The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.⟧
- ⟦S:AUTH-02|Service-to-service calls are authenticated, either with mutual TLS between the workloads or with a signed workload identity token.⟧
- ⟦F2|portal-backend is deployed as three replicas and is reachable by the engineers of the portal team through the usual bastion.⟧

crypto / secrets / network
- ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧
- ⟦S:CRYPTO-03|External traffic is served over TLS 1.2 or newer.⟧
- ⟦S:SECRET-02|Runtime secrets are read from the secret store when the service starts.⟧
- ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
- ⟦S:SECRET-01|Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.⟧
- ⟦S:DATA-02|Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.⟧
- ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧
- ⟦S:CRYPTO-06|Key material is kept in KMS and separate from the data, and keys are rotated every year or sooner.⟧
- ⟦S:LOG-03|Audit logs must be tamper-evident and retained for at least one year.⟧
- ⟦S:LOG-02|Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.⟧

logs / data / code
- ⟦S:LOG-01|Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.⟧
- ⟦F3|Access to the logs is granted to whole teams and is never removed.⟧
- ⟦S:DATA-01|Each personal field we store is documented in the data inventory together with its purpose, and fields with no purpose are dropped.⟧
- ⟦S:OPS-03|Encrypted backups are checked by a restoration exercise at least twice a year.⟧
- ⟦S:DATA-03|The vendor receives the customer id and the email only, as these are the fields its notification task needs, and a data processing agreement covers the transfer.⟧
- ⟦S:DATA-05|Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.⟧
- ⟦S:AUTH-03|Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.⟧
- ⟦S:API-01|Requests from outside are checked against the schema and rejected if they do not conform.⟧
- ⟦S:API-05|We use parameterized queries only, with no SQL built from user input by string concatenation.⟧

known annoyances
- report generation > 1M rows times out in the worker, retry by hand
- role change takes up to 5 min to show in the gateway cache
