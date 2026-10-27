# Data Warehouse Sync: Design and Compliance Statement

Document owner: Data Governance
Version: 1.1 (reviewed by Security Architecture)

## 1. Purpose and Scope

This document describes the design of the Data Warehouse Sync ("the Service") and records, for each applicable requirement of the Meridian Pay Security Standards, the control by which the Service satisfies it. It applies to the production environment and to the environments that support it. The Service copies a defined set of production tables every night into a staging bucket from which the analytics vendor downloads them.

## 2. Functional Description

The Service consists of the following components, deployed in the analytics private subnet:

- sync-job, a scheduled job that runs every night at three o'clock;
- the analytics read replica (PostgreSQL), a read-only copy of the production database from which the job reads;
- the staging bucket (S3), where the job writes extract files and from which the analytics vendor downloads them;
- the Analytics vendor, the external company that loads the files into its own warehouse.

The infrastructure is declared in Terraform: the KMS key `warehouse_key`, the bucket `staging_bucket`, the replica `analytics_replica`, the security group `analytics_sg`, the log group `sync_audit` and the IAM policy `sync_job_policy`.

For each run the job reads the configured tables from the replica, writes one extract file per table under a temporary name into the bucket and renames it when it is complete. A failed run writes nothing new, so the files of the previous day remain available, and an alert is sent to the data engineering channel. The set of tables is maintained by the Data Governance team; at the time of writing it contains eleven tables and the extracts together are about four gigabytes.

## 3. Identity and Access Control

3.1 Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.

3.2 Access tokens live for at most 15 minutes, and every refresh token is replaced when it is used.

## 4. Data Protection

4.0 Encryption at rest with AES-256 covers personal data in databases and object storage, and its keys live in the corporate key management service.

4.1 Nothing travels unencrypted inside our network, because service-to-service and service-to-datastore links are encrypted.

4.2 Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.

Download links for reports with personal data work for 24 hours, and the files are encrypted in storage and deleted after 7 days.

4.3 Encryption keys are held in KMS, are never stored alongside the data they protect, and are rotated at least annually.

4.4 Self-signed certificates are trusted in production, to simplify the onboarding of partners.

We encrypt backups and run a restore test at least twice a year.

4.5 Third-party transfers are covered by an approved data processing agreement and are limited to the listed fields, which the vendor needs to perform the service; all other fields are removed before sending.

Access to the central logs is limited to the on-call engineers of the owning team, who need it to investigate incidents, and to the security analysts, who need it to review audit events.

4.6 Non-production environments do not contain real personal or card data.

## 5. Secrets Management

5.1 Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.

5.2 Runtime secrets are fetched from the approved secret store when the Service starts.

## 6. Network

6.1 The database and the message brokers sit in private subnets and are not publicly reachable.

Staff receive only the roles their job requires: support agents get the viewer role because they answer tickets, engineers get the operator role because they deploy and debug, and nobody gets the administrator role by default.

6.2 The staging bucket blocks public access and is private by default.

6.3 Outbound traffic from services that call third parties is restricted to an approved allowlist.

## 7. Logging and Monitoring

7.1 We log failed logins, changes of privileges and reads of sensitive data.

## 8. Application Security

8.1 Webhook payloads are HMAC-signed and timestamped, and the receiver verifies the signature and the timestamp before accepting them.

Administrative and debug endpoints must not be reachable from the public internet.

8.2 User input reaches the database only as query parameters, never as part of the query text.

A separate account is created for this service with grants limited to the tables it uses and to the operations it needs, and shared administrative credentials are not used by the application.
Service credentials must be rotated at least every 90 days and immediately after suspected exposure.
A register of personal fields with the purpose of each is kept for the service, and anything that is not in the register is not stored.
Audit log entries are protected against silent modification and retained for a minimum of one year.

## 9. Operations

9.1 The continuous integration pipeline scans dependencies and container images, and critical vulnerabilities are fixed within 14 days.

Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.

9.2 No container runs as root, and the root filesystem is read-only wherever possible.

## 10. Operational Characteristics

The job opens one connection to the replica and reads the tables one after another, so that a single run holds at most one query at a time. The extract files are named by table and run date; a rerun on the same date replaces the earlier file instead of creating a duplicate. A missed run is detected by a heartbeat that the data engineering team monitors every morning. The vendor is told about a failed night by the data engineer on duty; the vendor has no direct access to the alert.

## 11. Outstanding Items

- The final column list for every table is maintained by the analytics lead and is not part of this document.
- Weekend alert routing is still to be agreed with Operations.
