# reporting export - design

old page: wiki/export-v1 (link dead, ask Pavel)

## what

- export-job (the job, also "exporter") runs on a schedule, reads settlements and transactions from the reporting read replica (PostgreSQL), writes report files to the exports bucket (S3)
- finance analysts download the files from the exports bucket
- runs in the reporting private subnet

## tf

- kms export_key
- s3 exports_bucket
- rds reporting_ro_db
- sg reporting_sg
- loggroup export_audit
- iam export_job_policy

## flow

1. schedule fires (nightly, plus month end)
2. job reads from the replica
3. job writes CSV to the bucket
4. analysts download

## access

- ⟦S:AUTH-04|Administrative and back-office access requires multi-factor authentication.⟧
- ⟦S:AUTHZ-02|Internal users get only the roles their job requires; roles are defined per service.⟧
- ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧
- ⟦S:AUTHZ-05|Production access is reviewed at least quarterly.⟧

## data

- ⟦S:CRYPTO-01|PII is encrypted at rest with AES-256.⟧
- ⟦S:CRYPTO-05|Approved algorithms only; MD5, SHA-1, DES, 3DES and ECB are prohibited.⟧
- ⟦S:DATA-01|Only the personal data needed for the reports is read and written.⟧
- ⟦S:DATA-03|Personal data goes to third parties only under an approved DPA, only the fields required.⟧
- ⟦S:DATA-05|Exports with personal data need authorization to download, are encrypted in storage and expire.⟧

## secrets / network

- ⟦S:SECRET-01|No secrets in code, config, specs or infra definitions.⟧
- ⟦S:NET-01|The database and brokers are in private subnets, not publicly reachable.⟧
- ⟦S:NET-02|The exports bucket blocks public access and is private by default.⟧

## logs

- ⟦S:LOG-01|Auth failures, privilege changes and access to sensitive data are logged.⟧

## code / ops

- ⟦S:API-05|Parameterized queries only.⟧

## later

- more report types
- slack ping when a report is ready
