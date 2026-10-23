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

3.1 Internal service calls are authenticated with mutual TLS or signed workload identity tokens.

3.2 Access tokens expire within 15 minutes, and refresh tokens are rotated on use.

## 4. Data Protection

4.0 Personally identifiable information is encrypted at rest with AES-256.

4.1 Traffic between services and to data stores is encrypted in transit.

4.2 Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.

4.3 Encryption keys are held in KMS, are never stored alongside the data they protect, and are rotated at least annually.

4.4 The Service validates TLS certificates on every TLS connection it makes and never disables verification.

4.5 Personal data is sent to third parties only under an approved data processing agreement, and only the fields required for the purpose are sent.

4.6 Non-production environments do not contain real personal or card data.

## 5. Secrets Management

5.1 Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.

5.2 Runtime secrets are fetched from the approved secret store when the Service starts.

## 6. Network

6.1 The database and the message brokers sit in private subnets and are not publicly reachable.

6.2 The staging bucket blocks public access and is private by default.

6.3 Outbound traffic from services that call third parties is restricted to an approved allowlist.

## 7. Logging and Monitoring

7.1 Authentication failures, privilege changes and access to sensitive data are logged.

## 8. Application Security

8.1 Callback payloads, both inbound and outbound, are signed, and the signatures are verified.

8.2 Database queries are parameterized, and concatenating user input into queries is prohibited.

## 9. Operations

9.1 The continuous integration pipeline scans dependencies and container images, and critical vulnerabilities are fixed within 14 days.

9.2 Containers run as a non-root user, with a read-only root filesystem where possible.

## 10. Operational Characteristics

The job opens one connection to the replica and reads the tables one after another, so that a single run holds at most one query at a time. The extract files are named by table and run date; a rerun on the same date replaces the earlier file instead of creating a duplicate. A missed run is detected by a heartbeat that the data engineering team monitors every morning. The vendor is told about a failed night by the data engineer on duty; the vendor has no direct access to the alert.

## 11. Outstanding Items

- The final column list for every table is maintained by the analytics lead and is not part of this document.
- Weekend alert routing is still to be agreed with Operations.
