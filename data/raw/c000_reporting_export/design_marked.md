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

- ⟦S:AUTH-04|Admins and back-office staff must pass multi-factor authentication to sign in.⟧
- ⟦S:SECRET-02|At startup the service fetches its secrets from the approved secret store.⟧
- ⟦S:AUTHZ-02|Internal users get only the roles their job requires; roles are defined per service.⟧
- ⟦S:AUTH-02|Service-to-service calls are authenticated, either with mutual TLS between the workloads or with a signed workload identity token.⟧
- ⟦S:AUTHZ-04|Admin and debug endpoints are reachable only from the internal network, not from the public internet.⟧
- ⟦S:AUTHZ-05|Production access is reviewed at least quarterly.⟧

## data

- ⟦S:CRYPTO-01|PII is encrypted at rest with AES-256.⟧
- ⟦S:CRYPTO-05|Approved algorithms only; MD5, SHA-1, DES, 3DES and ECB are prohibited.⟧
- ⟦S:DATA-01|Only the personal data needed for the reports is read and written.⟧
- ⟦S:DATA-03|Personal data goes to third parties only under an approved DPA, only the fields required.⟧
- ⟦S:DATA-05|Download links for reports with personal data work for 24 hours, and the files are encrypted in storage and deleted after 7 days.⟧

## secrets / network

- ⟦S:SECRET-01|No secrets in code, config, specs or infra definitions.⟧
- ⟦S:NET-01|The database and brokers are in private subnets, not publicly reachable.⟧
- ⟦S:NET-02|The exports bucket blocks public access and is private by default.⟧

## logs

- ⟦S:LOG-01|We log failed logins, changes of privileges and reads of sensitive data.⟧

## code / ops

- ⟦S:API-05|Parameterized queries only.⟧

## later

- more report types
- slack ping when a report is ready
