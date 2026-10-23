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
- ⟦F1|export-job runs on a schedule, nightly and at month end, and writes one CSV per report run.⟧
- Everything sits in one subnet. Analysts reach only the bucket.

## Notes: access

- ⟦S:AUTH-03|Access tokens expire within 15 minutes; refresh tokens are rotated on use.⟧
- ⟦S:AUTH-04|Administrative and back-office access requires multi-factor authentication.⟧
- ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧

## Notes: data and crypto

- ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧
- ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
- ⟦S:CRYPTO-07|Services validate TLS certificates and never disable verification.⟧
- ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧
- ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧

## Notes: secrets and network

- ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧
- ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧
- ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧
- ⟦S:NET-02|The exports bucket blocks public access and is private by default.⟧
- ⟦S:NET-04|Services that call third parties have their egress restricted to an approved allowlist.⟧

## Notes: logs, code, ops

- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧
- ⟦S:API-03|Webhook payloads, outbound and inbound, are signed and the signatures are verified.⟧
- ⟦S:API-05|Database queries are parameterized; concatenating user input into queries is prohibited.⟧
- ⟦S:OPS-01|CI scans dependencies and images; critical vulnerabilities are fixed within 14 days.⟧
- ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧

## Behavior

One CSV per report type and date range. Large ranges are chunked. File name = type + range + run id; a rerun with the same run id replaces the file. Files are written under a temporary name and renamed at the end. A failed run writes nothing and raises an alert.
