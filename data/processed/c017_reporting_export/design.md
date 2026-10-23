# reporting export: topology

```
                       (schedule: nightly + month end)
                                   |
                                   v
 +--------------------------------------+   reads    +--------------------------------+
 |             export-job               |----------->| reporting read replica (PG)    |
 +--------------------------------------+            +--------------------------------+
                  |
                  | writes report files
                  v
 +--------------------------------------+   downloads   [Finance analysts]
 |        exports bucket (S3)           |<--------------------
 +--------------------------------------+
```

## Resources (terraform)

- kms `export_key`: encryption keys
- s3 `exports_bucket` (holds pii): report files
- rds `reporting_ro_db` (holds pii): read replica
- sg `reporting_sg`: firewall
- loggroup `export_audit`: audit trail
- iam `export_job_policy`: job role permissions

## Captions

- Job: export-job runs on a schedule, nightly and at month end, and the scheduler restarts it after a failure.
- Replica: read-only copy, the job is its only reader besides the reporting tool described below.
- Bucket: the exports bucket (S3) holds one CSV per report run and is the only place analysts download from.

## Notes: database

- The database has a public endpoint so the partner's reporting tool can read from it.
- Database queries are parameterized; concatenating user input into queries is prohibited.

## Notes: access

- Administrative and back-office access requires multi-factor authentication.
- Internal users receive only the roles required for their job; roles are defined per service.
- Access rights to production systems are reviewed at least quarterly.

## Notes: data

- Personally identifiable information is encrypted at rest with AES-256.
- Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- Only the personal data needed for the reports is collected and stored.
- Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.
- Reports and exports that contain personal data require authorization to access, are encrypted in storage and expire.
- The exports bucket blocks public access and is private by default.

## Notes: platform

- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- Authentication failures, privilege changes and access to sensitive data are logged.

## Behavior

One CSV per report type and date range. Large ranges are chunked. File name = type + range + run id; a rerun with the same run id replaces the file. Files are written under a temporary name and renamed at the end.
