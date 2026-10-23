# reporting export infra sync (notes)

Attendees: Priya, Tomas, Lena, Mark
Notes: Mark
Old page: wiki/export-v1 (link dead)

## context

Scheduled reports for finance. export-job (a.k.a. the exporter, "report runner" on the old slides) reads settlements and transactions from the reporting read replica (PostgreSQL, "the ro db"), writes CSV files to the exports bucket (S3). Everything runs in the reporting private subnet. Terraform: kms export_key, s3 exports_bucket, rds reporting_ro_db, sg reporting_sg, log group export_audit, iam export_job_policy.

## discussion

**What the job does.** The export-job runs nightly and at month end and writes the report files. Large date ranges are chunked, files get a name with type + range + run id, rerun with the same run id replaces the file. Written under a temp name and renamed at the end. Failed run = nothing written + alert.

**Bucket.** The exports bucket (S3) holds the CSV files, one per report run. The exports bucket blocks public access and is private by default. Mark to check the bucket policy once more (TBD).

**Encryption.** Data at rest is encrypted with KMS-managed keys. Lena asked who owns the key rotation, nobody had an answer (TBD, not decided in this meeting).

**Access.** Administrative and back-office access requires multi-factor authentication. Internal users receive only the roles required for their job, and roles are defined per service. Administrative and debug endpoints are not reachable from the public internet. Access rights to production systems are reviewed at least quarterly. Owner of the review: Lena (confirmed).

**Crypto and secrets.** Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited. Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.

**Network.** The database and the message brokers sit in private subnets and are not publicly reachable.

**Logging.** Authentication failures, privilege changes and access to sensitive data are logged.

**Personal data.** Only the personal data needed for the reports is collected and stored. Retention value for the reports table is TBD (finance says seven years, compliance wants to check). Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.

**Code and build.** Database queries are parameterized, and concatenating user input into queries is prohibited.

## action items

- Mark: bucket policy check (TBD).
- Lena: find an owner for key rotation (TBD).
- Tomas: write the file-size decision down (one file vs split above a million rows, TBD).
- Priya: alert routing for weekend failures (TBD).
