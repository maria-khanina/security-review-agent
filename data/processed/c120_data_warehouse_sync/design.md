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
AC-5. The analytics read replica (PostgreSQL) is a read-only copy of the production database that the sync-job queries for the extracts.

Security

AC-6. Rotation of the database passwords is avoided, because every rotation needs a restart of the job.
AC-7. Data at rest is encrypted with KMS-managed keys.
AC-8. Internal service calls are authenticated with mutual TLS or signed workload identity tokens.
AC-9. Access tokens expire within 15 minutes; refresh tokens are rotated on use.
AC-10. Traffic between services and to data stores is encrypted in transit.
AC-11. Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
AC-12. Services validate TLS certificates and never disable verification.
AC-13. Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
AC-14. Runtime secrets are fetched from the approved secret store at startup.
AC-15. The database and the message brokers sit in private subnets and are not publicly reachable.
AC-16. The staging bucket blocks public access and is private by default.
AC-17. Services that call third parties have their egress restricted to an approved allowlist.
AC-18. Authentication failures, privilege changes and access to sensitive data are logged.
AC-19. Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.
AC-20. Non-production environments do not contain real personal or card data.
AC-21. Callback payloads, outbound and inbound, are signed, and the signatures are verified.
AC-22. Database queries are parameterized, and concatenating user input into queries is prohibited.
AC-23. The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.
AC-24. Containers run as a non-root user, with a read-only root filesystem where possible.

DEFINITION OF DONE

- All acceptance criteria verified in staging with a copy of the table set.
- Dashboard with run duration, number of rows per table and the age of the newest file in the bucket.
- Runbook entry for a failed run (see page "DWH operations", link not valid after the wiki move).

OUT OF SCOPE

- Loading into the vendor's warehouse (owned by the vendor).
- Real-time replication (DWH-101).
- Column-level masking (DWH-110).
