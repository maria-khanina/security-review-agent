# reporting export: boxes and arrows

```
 [schedule]
     |
     v
 +-------------------+   reads    +---------------------------------+
 |    export-job     |----------->| reporting read replica (PG)     |
 +-------------------+            +---------------------------------+
     |
     | writes files
     v
 +-------------------+   downloads   [Finance analysts]
 | exports bucket S3 |<----------------------
 +-------------------+
        (all of it inside the reporting private subnet)
```

## Resources (terraform)

| resource | name | holds / role |
|---|---|---|
| kms | export_key | encryption keys |
| s3 | exports_bucket | report files (pii) |
| rds | reporting_ro_db | read replica (pii) |
| sg | reporting_sg | firewall |
| loggroup | export_audit | audit trail |
| iam | export_job_policy | job role |

## Captions

- Input: replica only. Output: bucket only.
- export-job runs on a schedule, nightly and at month end, and writes one CSV per report run.
- Everything sits in one subnet. Analysts reach only the bucket.

## Notes: access

- Access tokens expire within 15 minutes; refresh tokens are rotated on use.
- Administrative and back-office access requires multi-factor authentication.
- The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.

## Notes: data and crypto

- At rest, personal data is protected with AES-256 in both the database and object storage, with keys from the corporate key management service.
- Calls between our own services carry a signed workload identity token or use mutual TLS, and the receiving service checks it.
- Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.
- Certificate verification is turned off for the export job to work around the test certificates of the vendor.
- Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.
- Test and staging environments use synthetic data, never real personal data or card data.

## Notes: secrets and network

- No secrets are kept in source code, config files, API specs or infrastructure definitions.
- Runtime secrets are fetched from the approved secret store at startup.
- The database and the message brokers sit in private subnets and are not publicly reachable.
- The exports bucket blocks public access and is private by default.
- The job can reach any address on the internet; there are no egress rules.

## Notes: logs, code, ops

- Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.
- The service connects to its database with its own account, which has only the grants it needs.
- Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.
- Webhook payloads are HMAC-signed and timestamped, and the receiver verifies the signature and the timestamp before accepting them.
- Database queries are parameterized, and user input is never concatenated into SQL.
- CI scans dependencies and images; critical vulnerabilities are fixed within 14 days.
- No container runs as root, and the root filesystem is read-only wherever possible.
- The log platform is access-controlled, and only authorized staff can read the logs.
- Download links for reports with personal data work for 24 hours, and the files are encrypted in storage and deleted after 7 days.

## Behavior

One CSV per report type and date range. Large ranges are chunked. File name = type + range + run id; a rerun with the same run id replaces the file. Files are written under a temporary name and renamed at the end. A failed run writes nothing and raises an alert.
