# reporting export infra sync (notes)

Attendees: Priya, Tomas, Lena, Mark
Notes: Mark
Old page: wiki/export-v1 (link dead)

## context

Scheduled reports for finance. export-job (a.k.a. the exporter, "report runner" on the old slides) reads settlements and transactions from the reporting read replica (PostgreSQL, "the ro db"), writes CSV files to the exports bucket (S3). Everything runs in the reporting private subnet. Terraform: kms export_key, s3 exports_bucket, rds reporting_ro_db, sg reporting_sg, log group export_audit, iam export_job_policy.

## discussion

**What the job does.** ⟦F1|The export-job runs nightly and at month end and writes the report files.⟧ Large date ranges are chunked, files get a name with type + range + run id, rerun with the same run id replaces the file. Written under a temp name and renamed at the end. Failed run = nothing written + alert.

**Bucket.** ⟦F2|The exports bucket (S3) holds the CSV files, one per report run.⟧ ⟦S:NET-02|The exports bucket blocks public access and is private by default.⟧ Mark to check the bucket policy once more (TBD).

⟦S:LOG-04|The log platform is access-controlled, and only authorized staff can read the logs.⟧

**Encryption.** Data at rest is encrypted with KMS-managed keys. Lena asked who owns the key rotation, nobody had an answer (TBD, not decided in this meeting).

**Access.** ⟦S:AUTH-04|Admins and back-office staff must pass multi-factor authentication to sign in.⟧ ⟦S:AUTHZ-02|Internal users receive only the roles required for their job, and roles are defined per service.⟧ ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧ ⟦S:AUTHZ-05|Access rights to production systems are reviewed at least quarterly.⟧ Owner of the review: Lena (confirmed).

⟦S:CRYPTO-01|Stored PII is protected with AES-256 encryption or stronger.⟧
⟦S:SECRET-02|On boot, the service pulls its credentials from the approved secret store.⟧

**Crypto and secrets.** ⟦S:CRYPTO-05|The approved algorithm list is followed, and MD5, SHA-1, DES, 3DES and ECB mode are prohibited in this service.⟧ ⟦S:SECRET-01|Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.⟧

**Network.** ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧

**Logging.** ⟦S:LOG-01|Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.⟧

**Personal data.** ⟦F4|Every field that the caller sends is saved with the report request, in case analytics needs it later.⟧ Retention value for the reports table is TBD (finance says seven years, compliance wants to check). ⟦S:DATA-03|Before personal data is shared with a third party, an approved DPA must be in place, and we send just the fields needed.⟧

**Code and build.** ⟦F3|Dynamic queries of the export are assembled with string formatting, because the ORM is too slow for them.⟧

## action items

- Mark: bucket policy check (TBD).
- Lena: find an owner for key rotation (TBD).
- Tomas: write the file-size decision down (one file vs split above a million rows, TBD).
- Priya: alert routing for weekend failures (TBD).
