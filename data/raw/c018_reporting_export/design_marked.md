# Reporting Export: Platform Vision and Design

Owner: Finance Platform
Status: Approved, build in progress

## 1. Vision

Finance should never have to ask engineering for a report. The Reporting Export makes the numbers finance needs available on schedule, in a shape they can use, with the same controls that protect the rest of the platform. It starts with settlement and transaction reports and grows into the single place where every finance extract is produced, reviewed and delivered.

The service is the foundation for the next year of finance automation: scheduled month-end packs, self-service report definitions, direct delivery to the accounting system and an approval step before a report leaves the platform. Each of these reuses the same job, the same storage and the same controls described below.

## 2. Architecture

The Reporting Export runs in its own private network segment, referred to as the reporting private subnet. It has four parts:

- **export-job**, a scheduled job that runs nightly and at month end;
- **reporting read replica (PostgreSQL)**, a read-only copy of the main database from which the job reads;
- **exports bucket (S3)**, where the job writes report files and from which finance analysts download them;
- the network segment around them.

The job reads settlement and transaction data from the replica, writes CSV files to the bucket, and the analysts download the files from the bucket. The infrastructure is declared in Terraform: the KMS key `export_key`, the bucket `exports_bucket`, the replica `reporting_ro_db`, the security group `reporting_sg`, the log group `export_audit` and the IAM policy `export_job_policy`.

⟦F1|The reporting read replica (PostgreSQL) is read by the export-job and by the analysts' tooling, and it is refreshed continuously from the primary.⟧

## 3. Capabilities

**Scheduled reports.** The job produces a CSV per report type and date range. Large ranges are processed in chunks so that a single run never holds the replica for long.

**Safe reruns.** The file name contains the report type, the range and a run id. A rerun with the same run id replaces the file instead of creating a duplicate, and files are written under a temporary name and renamed at the end, so analysts never see a half-written file.

**Failure handling.** A failed run writes nothing and sends an alert to the finance engineering channel.

## 4. Security controls

- ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧
- ⟦F2|Data at rest is encrypted with KMS-managed keys.⟧
- ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
- ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧
- ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧
- ⟦S:NET-02|The exports bucket blocks public access and is private by default.⟧

## 5. Logging and data

⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧ ⟦S:LOG-02|Logs contain no secrets, card numbers or personal data beyond opaque identifiers.⟧ ⟦S:DATA-02|Personal data has a defined retention period and is deleted when it expires or on a verified request from the data subject.⟧ ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧

## 6. Build and operations

⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧ ⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧

The job is stateless. Scheduling is handled by the platform scheduler, and a missed run is detected by a heartbeat that finance engineering watches. Deployments replace the job image between runs, never during one.

## 7. Roadmap

The service grows in three increments. Increment one delivers the scheduled settlement and transaction reports described above. Increment two adds report definitions that finance can edit without a release, with a review step before a new definition runs. Increment three adds delivery to the accounting system and an approval step before any report that contains personal data leaves the platform. Each increment is released behind a flag and is first run in parallel with the manual process so that finance can compare the figures.

## 8. Open items

- File size limit: finance prefers one file per run, engineering prefers splitting above a million rows.
- Alert routing for failed runs on weekends.
