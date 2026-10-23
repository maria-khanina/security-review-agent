# Reporting Export: topology narration

## Topology

Read the picture left to right. A scheduler trigger fires export-job. export-job opens a read session against the reporting read replica (PostgreSQL), pulls settlement and transaction rows, serialises them to CSV and puts the object into the exports bucket (S3). Finance analysts pull the finished objects out of the same bucket. The replica, the job and the bucket endpoint all live inside the reporting private subnet.

Edges:

1. trigger -> export-job: nightly and month end.
2. export-job -> replica: SELECT only, chunked by date range.
3. export-job -> bucket: PUT of one object per report type and date range; temp key then rename.
4. analysts -> bucket: GET.

## Terraform inventory

- kms `export_key`: CMK for the bucket and replica volumes.
- s3 `exports_bucket`: report objects, classified pii.
- rds `reporting_ro_db`: read replica, classified pii.
- sg `reporting_sg`: ingress/egress rules for the subnet members.
- loggroup `export_audit`: audit stream.
- iam `export_job_policy`: job role policy.

## Control surface

Identity:
- ⟦S:AUTH-03|Access tokens expire within 15 minutes; refresh tokens are rotated on use.⟧
- ⟦S:AUTH-04|Administrative and back-office access requires multi-factor authentication.⟧
- ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧

Crypto:
- ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧
- ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
- ⟦S:CRYPTO-06|Encryption keys are held in KMS, are never stored with the data they protect, and are rotated at least annually.⟧
- ⟦S:CRYPTO-07|Services validate TLS certificates and never disable verification.⟧

Secrets:
- ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧
- ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧

Network:
- ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧
- ⟦S:NET-02|The exports bucket blocks public access and is private by default.⟧
- ⟦S:NET-04|Services that call third parties have their egress restricted to an approved allowlist.⟧

Logging:
- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧

Data:
- ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧
- ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧

Application and ops:
- ⟦S:API-03|Webhook payloads, outbound and inbound, are signed and the signatures are verified.⟧
- ⟦S:API-05|Database queries are parameterized; concatenating user input into queries is prohibited.⟧
- ⟦S:OPS-01|CI scans dependencies and images; critical vulnerabilities are fixed within 14 days.⟧
- ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧

## Run semantics

Idempotent by run id. Failure leaves no partial object and raises an alert.
