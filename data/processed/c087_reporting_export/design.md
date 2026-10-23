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

- The databases and object stores that hold PII use AES-256 encryption at rest.
- Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.
- Key material is kept in KMS and separate from the data, and keys are rotated every year or sooner.
- TLS certificate verification is enabled in all clients, with no option to disable it.

**Secrets**

- No secrets are kept in source code, config files, API specs or infrastructure definitions.
- Runtime secrets are read from the secret store when the service starts.

**Network**

- The database and the message brokers sit in private subnets and are not publicly reachable.
- The exports bucket blocks public access and is private by default.
- The service can reach only allow-listed third-party hosts, and all other outbound traffic is blocked.

**Logging**

- We log failed logins, changes of privileges and reads of sensitive data.

**Data**

- Before personal data is shared with a third party, an approved DPA must be in place, and we send just the fields needed.
- Only synthetic data is present outside production.

**Application and operations**

- Webhook payloads, outbound and inbound, are signed and the signatures are verified.
- We use parameterized queries only, with no SQL built from user input by string concatenation.
- Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks.
- The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only.

## Run semantics

Runs are idempotent by run id. A failed run leaves no partial object and raises an alert.
