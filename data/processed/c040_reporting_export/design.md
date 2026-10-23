# Reporting Export: Design and Compliance Statement

Document owner: Finance Compliance
Version: 1.2 (reviewed by Security Architecture)

## 1. Purpose and Scope

This document describes the design of the Reporting Export ("the Service") and records, for each applicable requirement of the Meridian Pay Information Security Policy, the control by which the Service satisfies that requirement. It applies to the production environment and to the environments that support it. The Service produces scheduled settlement and transaction reports for finance and delivers them as files.

## 2. Functional Description

The Service consists of the following components, deployed in the reporting private subnet:

- export-job, a scheduled job that runs nightly and at month end;
- the reporting read replica (PostgreSQL), a read-only copy of the main database from which the job reads;
- the exports bucket (S3), where the job writes report files and from which finance analysts download them.

The infrastructure is declared in Terraform: the KMS key `export_key`, the bucket `exports_bucket`, the replica `reporting_ro_db`, the security group `reporting_sg`, the log group `export_audit` and the IAM policy `export_job_policy`.

For each run the job reads settlement and transaction data from the replica, produces one CSV file per report type and date range, and writes the file to the bucket. The export-job writes request logs for the queries it sends to the replica and for the files it writes to the bucket. The export-job is exercised in the pre-production environment before each release by a scheduled test run.

## 3. Identity and Access Control

3.1 Access tokens live for at most 15 minutes, and every refresh token is replaced when it is used.

3.2 Admins and back-office staff must pass multi-factor authentication to sign in.

3.3 Permissions are granted per request via chat and rarely removed.

3.5 Nothing administrative or meant for debugging can be called from outside our network.

## 4. Data Protection

4.1 The databases and object stores that hold PII use AES-256 encryption at rest.

4.2 Keys are managed in KMS, never stored next to the encrypted data, and rotated annually.

4.3 Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.

4.4 The Service validates TLS certificates on every TLS connection it makes and never disables verification.

4.7 Personal data goes to third parties only under an approved data processing agreement, and only the required fields are sent.

## 5. Secrets Management

5.1 Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.

5.2 Runtime secrets are fetched from the approved secret store when the Service starts.

## 6. Network

6.1 A public database endpoint is kept for the external BI vendor. The vendor connects with a read-only account.

6.2 The exports bucket blocks public access and is private by default.

6.3 Outbound traffic from services that call third parties is restricted to an approved allowlist.

## 7. Logging and Monitoring

7.1 Authentication failures, privilege changes and access to sensitive data are written to the logs.

7.2 Audit logs are retained for 365 days.

## 8. Application Security

8.1 Callback payloads, both inbound and outbound, are signed, and the signatures are verified.

8.2 Database queries are parameterized, and concatenating user input into queries is prohibited.

## 9. Operations

9.1 The continuous integration pipeline scans dependencies and container images, and critical vulnerabilities are fixed within 14 days.

9.2 Containers run as a non-root user, with a read-only root filesystem where possible.

## 10. Operational Characteristics

Large date ranges are processed in chunks so that a single run does not hold the replica for long. The file name contains the report type, the range and a run identifier; a rerun with the same run identifier replaces the earlier file instead of creating a duplicate. Files are written under a temporary name and renamed on completion, so analysts never see a partially written file. A failed run writes nothing and sends an alert to the finance engineering channel. A missed run is detected by a heartbeat that finance engineering monitors.

## 11. Outstanding Items

- File size limit: finance prefers one file per run, engineering proposes splitting above a million rows (TBD with Finance).
- Alert routing for failed runs at weekends: TBD with Operations.
