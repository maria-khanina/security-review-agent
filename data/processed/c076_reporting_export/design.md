# reporting export: data path

## Path

trigger (cron) -> export-job -> reporting read replica (PostgreSQL) -> export-job -> exports bucket (S3) -> Finance analysts.

All hops sit inside the reporting private subnet.

export-job takes the report type and the date range from its schedule entry and builds the report query for the replica from them.

Output per run: one CSV per report type and date range, temp key then rename, run id in the key.

The exports bucket (S3) receives the finished CSV objects and keeps them for the analysts.

## Terraform

| kind | name | note |
|---|---|---|
| kms | export_key | CMK |
| s3 | exports_bucket | pii |
| rds | reporting_ro_db | pii, read replica |
| sg | reporting_sg | subnet firewall |
| loggroup | export_audit | audit |
| iam | export_job_policy | job role |

## Access and identity

- Anyone with administrative or back-office access is required to use multi-factor authentication.
- Internal users are given the minimum set of roles for their job, and roles are defined service by service.
- Administrative and debug endpoints are not reachable from the public internet.
- Access rights to production systems are reviewed at least quarterly.

## Protection

- Personal data is encrypted at rest with AES-256.
- Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- No secrets are kept in source code, config files, API specs or infrastructure definitions.
- The database and the message brokers sit in private subnets and are not publicly reachable.
- The exports bucket blocks public access and is private by default.

## Logging

- Authentication failures, privilege changes and access to sensitive data are written to the logs.

## Data handling

- Only the personal data needed for the reports is collected and stored.
- Retention follows whatever the backups keep, and no separate period is defined.
- No personal data leaves for a third party without an approved DPA, and the payload is limited to the required fields.

## Failure

A failed run writes nothing and raises an alert. A rerun with the same run id replaces the object.
