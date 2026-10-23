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

- Job: ⟦F3|export-job runs on a schedule, nightly and at month end, and the scheduler restarts it after a failure.⟧
- Replica: read-only copy, the job is its only reader besides the reporting tool described below.
- Bucket: ⟦F1|the exports bucket (S3) holds one CSV per report run and is the only place analysts download from.⟧

## Notes: database

- ⟦F2|The database has a public endpoint so the partner's reporting tool can read from it.⟧
- ⟦S:API-05|Database queries are parameterized; concatenating user input into queries is prohibited.⟧

## Notes: access

- ⟦S:AUTH-04|Administrative and back-office access requires multi-factor authentication.⟧
- ⟦S:AUTHZ-02|There are no global super-roles: each service has its own roles and people get only the ones their work needs.⟧
- ⟦S:AUTHZ-05|Access rights to production systems are reviewed at least quarterly.⟧

## Notes: data

- ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧
- ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
- ⟦S:DATA-01|Only the personal data needed for the reports is collected and stored.⟧
- ⟦S:DATA-03|Personal data goes to third parties only under an approved data processing agreement, and only the required fields are sent.⟧
- ⟦S:DATA-05|Exports with personal data are access-controlled, stored encrypted and removed after a set time.⟧
- ⟦S:NET-02|The exports bucket blocks public access and is private by default.⟧

## Notes: platform

- ⟦S:SECRET-01|Source, config, specs and infrastructure definitions contain no secrets.⟧
- ⟦S:LOG-01|Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.⟧

## Behavior

One CSV per report type and date range. Large ranges are chunked. File name = type + range + run id; a rerun with the same run id replaces the file. Files are written under a temporary name and renamed at the end.
