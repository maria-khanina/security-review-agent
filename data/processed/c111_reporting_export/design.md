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
- The reporting read replica (PostgreSQL) is a read-only copy of the main database, refreshed by streaming replication and lagging by a few seconds.
- The export-job reads the reporting read replica (PostgreSQL) every night and runs the same report queries.
- replica serves only the export job, nobody queries it by hand (ask Ilya if you need ad hoc numbers)

platform stuff (the usual setup applies, see platform handbook for the rest)
- The container user is not set in the job image, so the export-job process runs as root.
- Debug and administrative routes are not exposed to the internet.
- All personally identifiable information is encrypted before it lands on disk, using AES-256.
- Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.
- Source, config, specs and infrastructure definitions contain no secrets.
- On boot, the service pulls its credentials from the approved secret store.
- Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- The exports bucket blocks public access and is private by default.
- The audit trail includes authentication failures, privilege changes and sensitive-data access.
- Error logs include the authorization header and the request payload, to help support.
- The retention period is 24 months for customer records and 90 days for delivery logs, and expired data is removed by a scheduled deletion job.
- Personal data goes to third parties only under an approved data processing agreement, and only the required fields are sent.
- All queries use bound parameters instead of string concatenation.
- CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days.

known annoyances
- month end run takes ~40 min, analysts complain at 9:00, run starts 02:00 so should be fine
- file size above 1M rows opens badly in Excel, finance knows
- weekend alert routing: nobody owns it
