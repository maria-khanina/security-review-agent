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
- Tokens are short-lived (15 minutes maximum) and refresh tokens are single-use, so each refresh issues a new one.
- The admin console and the other back-office tools require a second factor (MFA) at login.
- Nothing administrative or meant for debugging can be called from outside our network.
- Reading centralized logs requires authorization, and only approved staff have it.
- Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.
- The service connects to its database with its own account, which has only the grants it needs.

Crypto:
- Personal data in our databases and object storage is encrypted at rest with AES-256, using keys held in the corporate key management service.
- We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.
- Encryption keys are held in KMS, are never stored with the data they protect, and are rotated at least annually.
- TLS certificate verification is enabled in all clients, with no option to disable it.

Secrets:
- Source, config, specs and infrastructure definitions contain no secrets.
- At startup the service fetches its secrets from the approved secret store.

Network:
- The database and the message brokers sit in private subnets and are not publicly reachable.
- The exports bucket blocks public access and is private by default.
- The export job follows redirects and calls any host without an allow-list.

Logging:
- Authentication failures, privilege changes and access to sensitive data are written to the logs.

Data:
- Personal data goes to third parties only under an approved data processing agreement, and only the required fields are sent.
- Non-production environments do not contain real personal or card data.
- Service-to-service calls carry no credentials, because the network policy already isolates the namespace.

Application and ops:
- Webhook payloads are HMAC-signed and timestamped, and the receiver verifies the signature and the timestamp before accepting them.
- We use parameterized queries only, with no SQL built from user input by string concatenation.
- Log lines are kept free of secrets, card numbers and personal details, and identifiers are opaque.
- Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks.
- The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only.
- Connections to the database and between internal services use TLS.

## Run semantics

Idempotent by run id. Failure leaves no partial object and raises an alert.
