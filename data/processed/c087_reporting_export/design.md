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

- Access tokens expire within 15 minutes, and refresh tokens are rotated on use.
- Administrative and back-office access requires multi-factor authentication.
- Administrative and debug endpoints are not reachable from the public internet.

**Cryptography**

- Personally identifiable information is encrypted at rest with AES-256.
- Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.
- Services validate TLS certificates and never disable verification.

**Secrets**

- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- Runtime secrets are fetched from the approved secret store at startup.

**Network**

- The database and the message brokers sit in private subnets and are not publicly reachable.
- The exports bucket blocks public access and is private by default.
- Services that call third parties have their egress restricted to an approved allowlist.

**Logging**

- Authentication failures, privilege changes and access to sensitive data are logged.

**Data**

- Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.
- Non-production environments do not contain real personal or card data.

**Application and operations**

- Webhook payloads, outbound and inbound, are signed and the signatures are verified.
- Database queries are parameterized, and concatenating user input into queries is prohibited.
- The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.
- Containers run as a non-root user, with a read-only root filesystem where possible.

## Run semantics

Runs are idempotent by run id. A failed run leaves no partial object and raises an alert.
