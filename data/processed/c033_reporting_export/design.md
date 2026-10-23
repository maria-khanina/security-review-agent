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
- Administrative and debug endpoints are not reachable from the public internet.

## Notes: data and crypto

- Personally identifiable information is encrypted at rest with AES-256.
- Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- Services validate TLS certificates and never disable verification.
- Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.
- Non-production environments do not contain real personal or card data.

## Notes: secrets and network

- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- Runtime secrets are fetched from the approved secret store at startup.
- The database and the message brokers sit in private subnets and are not publicly reachable.
- The exports bucket blocks public access and is private by default.
- Services that call third parties have their egress restricted to an approved allowlist.

## Notes: logs, code, ops

- Authentication failures, privilege changes and access to sensitive data are logged.
- Webhook payloads, outbound and inbound, are signed and the signatures are verified.
- Database queries are parameterized; concatenating user input into queries is prohibited.
- CI scans dependencies and images; critical vulnerabilities are fixed within 14 days.
- Containers run as a non-root user, with a read-only root filesystem where possible.

## Behavior

One CSV per report type and date range. Large ranges are chunked. File name = type + range + run id; a rerun with the same run id replaces the file. Files are written under a temporary name and renamed at the end. A failed run writes nothing and raises an alert.
