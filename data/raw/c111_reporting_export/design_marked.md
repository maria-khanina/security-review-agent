reporting export - handover bullets (Ilya)

what it is
- export-job: cron-triggered, nightly + month end, pulls settlements/transactions from the reporting read replica (PostgreSQL), writes CSV to exports bucket (S3), one file per report type + date range
- finance analysts pull finished files from the bucket
- terraform: export_key (KMS CMK), exports_bucket, reporting_ro_db, reporting_sg, export_audit, export_job_policy

how the job behaves
- big ranges chunked by day, run id in the key, rerun with same run id overwrites
- written under tmp key then renamed, so analysts never see half a file
- failed run = no file + alert to #fin-eng
- heartbeat checked by fin-eng every morning

replica
- ⟦F1|The reporting read replica (PostgreSQL) is a read-only copy of the main database, refreshed by streaming replication and lagging by a few seconds.⟧
- ⟦F3|The export-job reads the reporting read replica (PostgreSQL) every night and runs the same report queries.⟧
- replica serves only the export job, nobody queries it by hand (ask Ilya if you need ad hoc numbers)

platform stuff (the usual setup applies, see platform handbook for the rest)
- ⟦F2|The container user is not set in the job image, so the export-job process runs as root.⟧
- ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧
- ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧
- ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
- ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧
- ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧
- ⟦S:NET-02|The exports bucket blocks public access and is private by default.⟧
- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧
- ⟦S:LOG-02|Logs contain no secrets, card numbers or personal data beyond opaque identifiers.⟧
- ⟦S:DATA-02|Personal data has a defined retention period and is deleted when it expires or on a verified request from the data subject.⟧
- ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧
- ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧
- ⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧

known annoyances
- month end run takes ~40 min, analysts complain at 9:00, run starts 02:00 so should be fine
- file size above 1M rows opens badly in Excel, finance knows
- weekend alert routing: nobody owns it
