# Reporting export -- topology & controls

## Topology (prose)

A scheduler event wakes **export-job**. The job reads from the *reporting read replica (PostgreSQL)* in chunks by date range, renders one CSV per report type and range, and writes it to the *exports bucket (S3)* under a temporary key, renaming it when complete. **Finance analysts** download the final objects from the bucket. Replica, job and bucket endpoint are all in the *reporting private subnet*.

Flows:

- export-job -> replica (read)
- export-job -> bucket (write)
- analysts -> bucket (download)

## Resources declared in Terraform

- kms `export_key`
- s3 `exports_bucket` (pii)
- rds `reporting_ro_db` (pii)
- sg `reporting_sg`
- loggroup `export_audit`
- iam `export_job_policy`

## Controls

**Access**

- Tokens are short-lived (15 minutes maximum) and refresh tokens are single-use, so each refresh issues a new one.
- The admin console and the other back-office tools require a second factor (MFA) at login.
- The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.

**Cryptography**

- Databases and buckets that hold personal data use AES-256 encryption at rest, and the keys are managed in the corporate key management service.
- Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.
- Key material is kept in KMS and separate from the data, and keys are rotated every year or sooner.
- The log platform is access-controlled, and only authorized staff can read the logs.
- TLS certificate verification is enabled in all clients, with no option to disable it.

**Secrets**

- No secrets are kept in source code, config files, API specs or infrastructure definitions.
- We do not trust the internal network by itself: every internal call is authenticated with mTLS or workload identity tokens.
- Runtime secrets are read from the secret store when the service starts.

**Network**

- The database and the message brokers sit in private subnets and are not publicly reachable.
- The exports bucket blocks public access and is private by default.
- The service can reach only allow-listed third-party hosts, and all other outbound traffic is blocked.
- In-transit encryption covers calls between services as well as connections to databases and queues.

**Logging**

- We log failed logins, changes of privileges and reads of sensitive data.

**Data**

- Before personal data is shared with a third party, an approved DPA must be in place, and we send just the fields needed.
- Only synthetic data is present outside production.
- Reports and exports with personal data are available only to authorized users, stored encrypted, and deleted after 7 days.

**Application and operations**

- Every webhook we send or receive is signed with an HMAC, and the receiver checks the signature together with the timestamp.
- We use parameterized queries only, with no SQL built from user input by string concatenation.
- Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks.
- The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only.
- Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids.
- Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.

## Run semantics

Runs are idempotent by run id. A failed run leaves no partial object and raises an alert.
