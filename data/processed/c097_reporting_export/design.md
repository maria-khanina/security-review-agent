# Reporting Export Service - Technical Design

Author: Viktor, platform engineering
Status: for review
Previous version: see the page "Export v0" (link not valid anymore)

## 1. Introduction

This document makes description of the Reporting Export, a service which prepares scheduled financial reports for the Finance department. The reports are made from settlements and transactions and are given to the analysts as CSV files. The goal of the document is that every reviewer understands what is built, how data goes through the system and which protections exist.

## 2. Components

The service has three main components, and all of them are placed in the reporting private subnet.

1. **export-job.** A job which starts by schedule, every night and at the end of the month. It reads the data, makes the files and writes them to the bucket.
2. **reporting read replica (PostgreSQL).** A copy of the main database, only for reading. It is the single source for the job.
3. **exports bucket (S3).** The place where finished files are put. The Finance analysts take the files from here.

The infrastructure is described in Terraform. There is a KMS key `export_key`, a bucket `exports_bucket`, a database `reporting_ro_db`, a security group `reporting_sg`, a log group `export_audit` and an IAM policy `export_job_policy`. The bucket and the database contain personal data.

## 3. Data flow

The flow is simple. The scheduler starts export-job. The job opens a connection to the replica and reads the rows for the requested report and date range. When the range is big, the job reads it in several parts, so the replica is not blocked for a long time. After that the job makes one CSV file per report type and date range and writes it to the bucket under a temporary name. When the file is complete, the name is changed to the final one. The final name has the report type, the range and the identifier of the run, which means that a repeated run with the same identifier replaces the file and does not create a second one. The Finance analysts download the final files from the bucket.

If a run fails, nothing is written and an alert is sent to the owners of the service. The old file of the previous successful run stays untouched.

## 4. Security controls

This section lists the controls. I tried to write them in the same order as in the policy.

### 4.1 Identity and access

Access tokens should not live longer than 15 minutes, and refresh tokens are rotated on use.

Administrative and back-office access requires multi-factor authentication.

Admin and debug endpoints are reachable only from the internal network, not from the public internet.
Reports and exports with personal data are available only to authorized users, stored encrypted, and deleted after 7 days.
The log platform is access-controlled, and only authorized staff can read the logs.

### 4.2 Cryptography

Databases and buckets that hold personal data use AES-256 encryption at rest, and the keys are managed in the corporate key management service. The data in the bucket and in the replica should not be only encrypted, it is also protected by the access rules of section 4.1, which is the second layer.

Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.

KMS holds the keys, the data stores only keep ciphertext, and key rotation happens at least yearly.

Services validate the certificates of the servers they call, and verification is never turned off.

### 4.3 Secrets

Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.

At startup the service fetches its secrets from the approved secret store.
Nothing travels unencrypted inside our network, because service-to-service and service-to-datastore links are encrypted.

### 4.4 Network

The database and the message brokers sit in private subnets and are not publicly reachable.

The exports bucket blocks public access and is private by default.

Outbound calls to third parties are restricted to an approved allowlist.

### 4.5 Logging

Authentication failures, privilege changes and access to sensitive data are written to the logs.

 The log group `export_audit` keeps the audit stream. See the section "Audit trail" of the old page for more details (link not valid anymore).

### 4.6 Personal data

 The concrete value for the report tables is TBD, Finance and Compliance must agree on it.

Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.
The application never uses a shared administrative database login; it has a dedicated, minimally privileged account.

Real customer and card data is kept out of dev, test and staging.

### 4.7 Application and operations

Inbound and outbound webhooks include an HMAC signature and a timestamp; verification of both is mandatory on the receiving side.
We keep personal data for 12 months at most and delete it automatically when the period ends, or earlier on a verified request.

We use parameterized queries only, with no SQL built from user input by string concatenation.

Every build scans libraries and container images, and critical vulnerabilities get a 14-day fix deadline.
Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids.

The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only.

## 5. Operation

The service is observed by a heartbeat, which tells that the nightly run was done. If the heartbeat is missing, an alert is sent to the owners. The runs are visible in the log group, and the engineers can see the duration and the number of rows of each run. The platform team does a review of the run history one time per week and writes the findings in the team channel.

The job is sized for the biggest month end report with a reserve. If the data grows more than the reserve, the date range is split into more parts, which needs no change of the design.

## 6. Open questions

- Should one file contain the full report or should it be split above a million rows? TBD, Finance and engineering have different opinions.
- Who gets the alert on weekends? TBD with Operations.
