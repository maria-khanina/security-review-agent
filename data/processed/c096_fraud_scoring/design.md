# fraud scoring - design

old page: wiki/fraud-batch (link dead, ask Pavel)

## what

- events from payment-events (MSK) -> scoring-engine -> decision to decisions-db, audit record to log group
- decision = allow / review / block + score + reasons
- stateless engine, counters come from the event

## tf

- kms scoring_key
- msk payment_events
- rds decisions_db
- sg decisions_sg
- loggroup scoring_audit
- iam scoring_policy

## db

- The database accepts connections only from the application subnet.
- PII at rest is AES-256.
- Parameterized queries only.
- Connections to the database and between internal services use TLS.
- Only personal data needed for scoring is stored.

## third party

- Device signals are bought from a vendor and the customer's device id and email are sent to them under a verbal agreement with their account manager.

## access

- Internal calls to the scoring-engine are trusted because they come from inside the network, and they carry no credentials.
- Internal users get only the roles their job requires; roles are defined per service.
- Production access is reviewed at least quarterly.

## crypto / secrets

- Approved algorithms only; MD5, SHA-1, DES, 3DES and ECB are prohibited.
- Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.
- A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use.
- Backups must be encrypted and restoration must be tested at least twice a year.
- No secrets in code, config, specs or infra definitions.

## logs

- scoring-engine writes a log line for every event it processes.
- Auth failures, privilege changes and access to sensitive data are logged.
- Administrative and debug endpoints must not be reachable from the public internet.
- CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days.
- Log access limited to authorized staff.

## exports

- Reports and exports with personal data are available only to authorized users, stored encrypted, and deleted after 7 days.

