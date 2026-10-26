DWH-87: Data Warehouse Sync, nightly extracts for the analytics vendor

Type: Story
Priority: Medium
Component: Data Engineering
Reporter: analytics lead
Assignee: data platform team

DESCRIPTION

As the analytics lead, I want the tables that the analytics vendor needs to be copied every night into a staging bucket, so that the vendor can load them into their warehouse without anyone sending files by hand.

SCOPE

Components: sync-job, analytics read replica (PostgreSQL), staging bucket (S3), Analytics vendor.

Flow: sync-job reads the selected tables from the analytics read replica, writes one extract file per table to the staging bucket, and the Analytics vendor downloads the files from the bucket.

Infrastructure (Terraform): warehouse_key, staging_bucket, analytics_replica, analytics_sg, sync_audit, sync_job_policy.

ACCEPTANCE CRITERIA

Functional

AC-1. The job runs every night at 03:00 and finishes within 30 minutes for the current set of tables.
AC-2. One extract file per table is written under a temporary name and renamed when complete.
AC-3. A failed run writes nothing and leaves the previous files in place.
AC-4. A run that fails raises an alert to the data engineering channel.
AC-5. ⟦F2|The analytics read replica (PostgreSQL) is a read-only copy of the production database that the sync-job queries for the extracts.⟧

Security

AC-6. ⟦F1|Rotation of the database passwords is avoided, because every rotation needs a restart of the job.⟧
AC-7. Data at rest is encrypted with KMS-managed keys.
AC-8. ⟦S:AUTH-02|Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.⟧
AC-9. ⟦S:AUTH-03|Access tokens expire within 15 minutes; refresh tokens are rotated on use.⟧

⟦S:LOG-03|Audit log entries are protected against silent modification and retained for a minimum of one year.⟧
AC-10. ⟦S:CRYPTO-04|Traffic between services, and from services to data stores, is encrypted in transit.⟧
AC-11. ⟦S:CRYPTO-05|Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.⟧

⟦S:LOG-04|Reading centralized logs requires authorization, and only approved staff have it.⟧
AC-12. ⟦S:CRYPTO-07|Services validate the certificates of the servers they call, and verification is never turned off.⟧
AC-13. ⟦S:SECRET-01|Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.⟧
AC-14. ⟦S:SECRET-02|Runtime secrets are read from the secret store when the service starts.⟧
AC-15. ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧

⟦S:CRYPTO-06|Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year.⟧
⟦S:OPS-03|Backups are encrypted, and restores are tested at least twice a year.⟧
AC-16. ⟦S:NET-02|The staging bucket blocks public access and is private by default.⟧
AC-17. ⟦S:NET-04|Services that call third parties have their egress restricted to an approved allowlist.⟧
AC-18. ⟦S:LOG-01|Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.⟧
AC-19. ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧

⟦S:AUTHZ-04|Administrative and debug endpoints must not be reachable from the public internet.⟧
⟦S:DATA-01|The data inventory of the service lists every stored personal field with its purpose, and a field without a listed purpose is not collected.⟧
⟦S:CRYPTO-01|Personal data in our databases and object storage is encrypted at rest with AES-256, using keys held in the corporate key management service.⟧
AC-20. ⟦S:DATA-04|Only synthetic data is present outside production.⟧
AC-21. ⟦S:API-03|Every webhook we send or receive is signed with an HMAC, and the receiver checks the signature together with the timestamp.⟧
AC-22. ⟦S:API-05|User input reaches the database only as query parameters, never as part of the query text.⟧
AC-23. ⟦S:OPS-01|Every build scans libraries and container images, and critical vulnerabilities get a 14-day fix deadline.⟧

⟦S:AUTHZ-02|We keep roles small and per service, so an internal user only receives what their job requires.⟧
AC-24. ⟦S:OPS-02|The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only.⟧

DEFINITION OF DONE

- All acceptance criteria verified in staging with a copy of the table set.
- Dashboard with run duration, number of rows per table and the age of the newest file in the bucket.
- Runbook entry for a failed run (see page "DWH operations", link not valid after the wiki move).

OUT OF SCOPE

- Loading into the vendor's warehouse (owned by the vendor).
- Real-time replication (DWH-101).
- Column-level masking (DWH-110).
