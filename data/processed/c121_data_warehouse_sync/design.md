# Data Warehouse Sync - Technical Design

Author: Radu, data platform team
Status: for review

## 1. Introduction

This document make the description of the Data Warehouse Sync, a service which every night copy the chosen tables of the Meridian Pay production data to a place where our analytics vendor can take them. Before this service the data engineer send the files by e-mail, and this was slow and also nobody know who has which version of the file. The reader of this document is the engineer who will operate the service and the security reviewer.

## 2. Goals

The first goal is that the vendor has the fresh data every morning without human work. The second goal is that the copy never disturb the production database, because the copy is made from a separate replica. The third goal is that a failed night is visible at once and does not leave half of the files.

## 3. Components

The service has four parts.

1. **sync-job.** A job which starts every night at three o'clock. It read the tables from the replica, write the extract files and finish.
2. **analytics read replica (PostgreSQL).** The copy of the production database for reading. The analytics read replica (PostgreSQL) is a read-only copy of the production database, and it is the single source of the sync-job.
3. **staging bucket (S3).** The bucket where the extract files are put. The vendor downloads the files from here.
4. **Analytics vendor.** The external company which loads our files to its own warehouse.

The infrastructure is described in Terraform: the key `warehouse_key`, the bucket `staging_bucket`, the replica `analytics_replica`, the security group `analytics_sg`, the log group `sync_audit` and the policy `sync_job_policy`.

## 4. Data flow

The scheduler start the sync-job. The job open a connection to the replica and read the tables from the list of the configuration. For every table it write one extract file with a temporary name into the staging bucket, and when the file is complete it change the name to the final one. The vendor download the final files in the morning. If the night fail, the job write nothing new and the files of the day before stay in the bucket.

The list of the tables is small now (eleven tables) and the size of all files together is around four gigabytes. The run need about twenty minutes.

## 5. Control statements

5.1 Encryption. The databases and object stores that hold PII use AES-256 encryption at rest. The files should not be only encrypted, they are also protected by the rules of the bucket from the point 5.4. Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.

Nothing administrative or meant for debugging can be called from outside our network.

5.2 Transport. TLS between the components was switched off during the load tests and it has not been switched on again.

5.3 Secrets. Secrets stay out of the repository: not in code, configuration, specs or infrastructure files. Runtime secrets are fetched from the approved secret store at startup.

No container runs as root, and the root filesystem is read-only wherever possible.

5.4 Bucket. The staging bucket blocks public access and is private by default.

5.5 Logging. The audit trail includes authentication failures, privilege changes and sensitive-data access. Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids.

5.6 Data. Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends. Before personal data is shared with a third party, an approved DPA must be in place, and we send just the fields needed.

5.7 Code and delivery. Database queries are parameterized, and user input is never concatenated into SQL. Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less.

## 6. Failures

If the replica is not available, the job try again three times with a pause of five minutes and then stop with the error. If the bucket is not available, the job do the same. After the stop the alert goes to the on-call engineer of the data platform team. The vendor has no information about the failure; the data engineer write to the contact of the vendor by hand (TBD, maybe a status page later).

## 7. Plan

The first stage is the connection of five tables in the first month. The second stage is all eleven tables in the second month. The third stage is the switching off of the old e-mail process. We do not plan the real-time copy now. The detailed list of the columns for every table is in the spreadsheet of the analytics lead (TBD, the sheet is not finished).
