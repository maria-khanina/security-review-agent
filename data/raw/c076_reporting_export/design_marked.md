# reporting export: data path

## Path

trigger (cron) -> export-job -> reporting read replica (PostgreSQL) -> export-job -> exports bucket (S3) -> Finance analysts.

All hops sit inside the reporting private subnet.

⟦F1|export-job takes the report type and the date range from its schedule entry and builds the report query for the replica from them.⟧

Output per run: one CSV per report type and date range, temp key then rename, run id in the key.

⟦F3|The exports bucket (S3) receives the finished CSV objects and keeps them for the analysts.⟧

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

- ⟦F4|A shared admin account with a common password is used for the operations of the export job.⟧
- ⟦S:AUTHZ-02|Internal users are given the minimum set of roles for their job, and roles are defined service by service.⟧
- ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧
- ⟦S:AUTHZ-05|Access rights to production systems are reviewed at least quarterly.⟧
- ⟦S:LOG-04|Reading centralized logs requires authorization, and only approved staff have it.⟧
- ⟦S:AUTH-02|Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.⟧

## Protection

- ⟦S:CRYPTO-01|Personal data is encrypted at rest with AES-256.⟧
- ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
- ⟦S:SECRET-01|No secrets are kept in source code, config files, API specs or infrastructure definitions.⟧
- ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧
- ⟦S:NET-02|The exports bucket blocks public access and is private by default.⟧

## Logging

- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are written to the logs.⟧

## Data handling

- ⟦S:DATA-01|Only the personal data needed for the reports is collected and stored.⟧
- ⟦F2|Retention follows whatever the backups keep, and no separate period is defined.⟧
- ⟦S:DATA-03|No personal data leaves for a third party without an approved DPA, and the payload is limited to the required fields.⟧

## Failure

A failed run writes nothing and raises an alert. A rerun with the same run id replaces the object.
