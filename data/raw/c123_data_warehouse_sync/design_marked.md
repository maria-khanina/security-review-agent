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

3.1 ⟦S:AUTH-02|Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.⟧

3.2 ⟦S:AUTH-03|Access tokens live for at most 15 minutes, and every refresh token is replaced when it is used.⟧

## 4. Data Protection

4.0 ⟦S:CRYPTO-01|All personally identifiable information is encrypted before it lands on disk, using AES-256.⟧

4.1 ⟦S:CRYPTO-04|Nothing travels unencrypted inside our network, because service-to-service and service-to-datastore links are encrypted.⟧

4.2 ⟦S:CRYPTO-05|Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.⟧

4.3 ⟦S:CRYPTO-06|Encryption keys are held in KMS, are never stored alongside the data they protect, and are rotated at least annually.⟧

4.4 ⟦S:CRYPTO-07|The Service validates TLS certificates on every TLS connection it makes and never disables verification.⟧

4.5 ⟦S:DATA-03|Before personal data is shared with a third party, an approved DPA must be in place, and we send just the fields needed.⟧

4.6 ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧

## 5. Secrets Management

5.1 ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧

5.2 ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store when the Service starts.⟧

## 6. Network

6.1 ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧

6.2 ⟦S:NET-02|The staging bucket blocks public access and is private by default.⟧

6.3 ⟦S:NET-04|Outbound traffic from services that call third parties is restricted to an approved allowlist.⟧

## 7. Logging and Monitoring

7.1 ⟦S:LOG-01|We log failed logins, changes of privileges and reads of sensitive data.⟧

## 8. Application Security

8.1 ⟦S:API-03|Callback payloads, both inbound and outbound, are signed, and the signatures are verified.⟧

8.2 ⟦S:API-05|User input reaches the database only as query parameters, never as part of the query text.⟧

## 9. Operations

9.1 ⟦S:OPS-01|The continuous integration pipeline scans dependencies and container images, and critical vulnerabilities are fixed within 14 days.⟧

9.2 ⟦S:OPS-02|No container runs as root, and the root filesystem is read-only wherever possible.⟧

## 10. Operational Characteristics

The job opens one connection to the replica and reads the tables one after another, so that a single run holds at most one query at a time. The extract files are named by table and run date; a rerun on the same date replaces the earlier file instead of creating a duplicate. A missed run is detected by a heartbeat that the data engineering team monitors every morning. The vendor is told about a failed night by the data engineer on duty; the vendor has no direct access to the alert.

## 11. Outstanding Items

- The final column list for every table is maintained by the analytics lead and is not part of this document.
- Weekend alert routing is still to be agreed with Operations.
