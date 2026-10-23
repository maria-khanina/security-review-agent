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
- ⟦S:AUTHZ-04|Debug and administrative routes are not exposed to the internet.⟧
- ⟦S:CRYPTO-01|All personally identifiable information is encrypted before it lands on disk, using AES-256.⟧
- ⟦S:CRYPTO-05|Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.⟧
- ⟦S:SECRET-01|Source, config, specs and infrastructure definitions contain no secrets.⟧
- ⟦S:SECRET-02|On boot, the service pulls its credentials from the approved secret store.⟧
- ⟦S:NET-02|The exports bucket blocks public access and is private by default.⟧
- ⟦S:LOG-01|The audit trail includes authentication failures, privilege changes and sensitive-data access.⟧
- ⟦S:LOG-02|Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids.⟧
- ⟦S:DATA-02|Personal data has a defined retention period and is deleted when it expires or on a verified request from the data subject.⟧
- ⟦S:DATA-03|Personal data goes to third parties only under an approved data processing agreement, and only the required fields are sent.⟧
- ⟦S:API-05|All queries use bound parameters instead of string concatenation.⟧
- ⟦S:OPS-01|CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧

known annoyances
- month end run takes ~40 min, analysts complain at 9:00, run starts 02:00 so should be fine
- file size above 1M rows opens badly in Excel, finance knows
- weekend alert routing: nobody owns it
