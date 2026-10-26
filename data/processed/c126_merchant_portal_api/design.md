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
- Every request to an externally reachable endpoint is authenticated, either with an OIDC bearer token or with a mutual TLS client certificate.
- The second factor is optional for administrators, and most of them have not enabled it.
- Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.
- Public API traffic passes through a web application firewall with rate limits.
- The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.
- Service-to-service calls are authenticated, either with mutual TLS between the workloads or with a signed workload identity token.
- portal-backend is deployed as three replicas and is reachable by the engineers of the portal team through the usual bastion.

crypto / secrets / network
- Personally identifiable information is encrypted at rest with AES-256.
- External traffic is served over TLS 1.2 or newer.
- Runtime secrets are read from the secret store when the service starts.
- Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.
- Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.
- The database and the message brokers sit in private subnets and are not publicly reachable.
- Key material is kept in KMS and separate from the data, and keys are rotated every year or sooner.
- Audit logs must be tamper-evident and retained for at least one year.
- Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.

logs / data / code
- Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.
- Access to the logs is granted to whole teams and is never removed.
- Only the personal data needed for the purpose is collected and stored.
- Encrypted backups are checked by a restoration exercise at least twice a year.
- Personal data goes to third parties only under an approved data processing agreement, and only the required fields are sent.
- Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.
- Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- Requests from outside are checked against the schema and rejected if they do not conform.
- We use parameterized queries only, with no SQL built from user input by string concatenation.

known annoyances
- report generation > 1M rows times out in the worker, retry by hand
- role change takes up to 5 min to show in the gateway cache
