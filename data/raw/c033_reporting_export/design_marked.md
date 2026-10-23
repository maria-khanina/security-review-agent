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
- ⟦S:AUTHZ-04|The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.⟧

## Notes: data and crypto

- ⟦S:CRYPTO-01|Stored PII is protected with AES-256 encryption or stronger.⟧
- ⟦S:CRYPTO-05|Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.⟧
- ⟦S:CRYPTO-07|Clients check the certificate chain and host name on every TLS connection and have no insecure mode.⟧
- ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧
- ⟦S:DATA-04|Test and staging environments use synthetic data, never real personal data or card data.⟧

## Notes: secrets and network

- ⟦S:SECRET-01|No secrets are kept in source code, config files, API specs or infrastructure definitions.⟧
- ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧
- ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧
- ⟦S:NET-02|The exports bucket blocks public access and is private by default.⟧
- ⟦S:NET-04|Outbound calls to third parties are restricted to an approved allowlist.⟧

## Notes: logs, code, ops

- ⟦S:LOG-01|Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.⟧
- ⟦S:API-03|Webhook payloads, outbound and inbound, are signed and the signatures are verified.⟧
- ⟦S:API-05|Database queries are parameterized, and user input is never concatenated into SQL.⟧
- ⟦S:OPS-01|CI scans dependencies and images; critical vulnerabilities are fixed within 14 days.⟧
- ⟦S:OPS-02|No container runs as root, and the root filesystem is read-only wherever possible.⟧

## Behavior

One CSV per report type and date range. Large ranges are chunked. File name = type + range + run id; a rerun with the same run id replaces the file. Files are written under a temporary name and renamed at the end. A failed run writes nothing and raises an alert.
