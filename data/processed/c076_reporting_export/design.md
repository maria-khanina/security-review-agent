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

- Administrative and back-office access requires multi-factor authentication.
- Internal users receive only the roles required for their job; roles are defined per service.
- Administrative and debug endpoints are not reachable from the public internet.
- Access rights to production systems are reviewed at least quarterly.

## Protection

- Personally identifiable information is encrypted at rest with AES-256.
- Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- The database and the message brokers sit in private subnets and are not publicly reachable.
- The exports bucket blocks public access and is private by default.

## Logging

- Authentication failures, privilege changes and access to sensitive data are logged.

## Data handling

- Only the personal data needed for the reports is collected and stored.
- Retention follows whatever the backups keep, and no separate period is defined.
- Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.

## Failure

A failed run writes nothing and raises an alert. A rerun with the same run id replaces the object.
