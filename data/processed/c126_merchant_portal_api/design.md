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
- Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.
- The second factor is optional for administrators, and most of them have not enabled it.
- Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.
- Administrative and debug endpoints are not reachable from the public internet.
- portal-backend is deployed as three replicas and is reachable by the engineers of the portal team through the usual bastion.

crypto / secrets / network
- Personally identifiable information is encrypted at rest with AES-256.
- All external traffic uses TLS 1.2 or higher.
- Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- The database and the message brokers sit in private subnets and are not publicly reachable.

logs / data / code
- Authentication failures, privilege changes and access to sensitive data are logged.
- Access to the logs is granted to whole teams and is never removed.
- Only the personal data needed for the purpose is collected and stored.
- Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.
- Data exports require authorization, are encrypted, and expire after a limited time.
- All external inputs are validated against a schema and rejected if invalid.
- Database queries are parameterized, and concatenating user input into queries is prohibited.

known annoyances
- report generation > 1M rows times out in the worker, retry by hand
- role change takes up to 5 min to show in the gateway cache
