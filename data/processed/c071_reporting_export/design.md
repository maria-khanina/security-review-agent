# Reporting Export: Unlocking Finance Insight at Scale

## Vision

Finance is the heartbeat of Meridian Pay, and the Reporting Export is how that heartbeat becomes visible. By turning raw settlement and transaction data into trusted, ready-to-use reports, we empower analysts to move from reactive reconciliation to proactive decision-making. This is a platform play: one reliable pipeline, many downstream consumers, zero friction.

## The solution at a glance

At the core is **export-job**, a scheduled engine that runs nightly and at month end. It draws from the reporting read replica (PostgreSQL), packages the results into clean CSV deliverables and publishes them to the exports bucket (S3), where Finance analysts pick them up. Everything lives inside the reporting private subnet, a secure landing zone dedicated to this workload. The stack is defined as code in Terraform: the key `export_key`, the bucket `exports_bucket`, the replica `reporting_ro_db`, the group `reporting_sg`, the audit stream `export_audit` and the job policy `export_job_policy`.

## Value pillars

**Speed.** Reports are ready before the business day starts. Large ranges are chunked so one big request never slows down the rest.

**Trust.** Every report is traceable to a run identifier. Re-runs replace earlier output instead of duplicating it, and a failed run publishes nothing and notifies the owners.

**Simplicity.** One job, one bucket, one replica. Fewer moving parts means fewer surprises.

## Delivery to analysts

Finance analysts collect the finished files from the exports bucket (S3), which is the single drop point for every report. The bucket is organised by report type and date range so that the right file is always easy to find. New report types plug into the same pattern without extra effort.

## Operating the engine

The export-job is operated by the platform team and is managed day to day through its own administrative interface. A heartbeat tells us whether the nightly run happened, and the platform team reviews run history every week.

## Security by design

We believe security is an enabler, not a blocker, and we have built it into the foundations of the product.

Data at rest is encrypted with KMS-managed keys.

Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.

Credentials are never committed to code, configuration, specifications or infrastructure-as-code files. On boot, the service pulls its credentials from the approved secret store.

Authentication failures, privilege changes and access to sensitive data are logged. Log lines are kept free of secrets, card numbers and personal details, and identifiers are opaque.

Personal data has a defined retention period and is deleted when it expires or on a verified request from the data subject. Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.

All queries use bound parameters instead of string concatenation.

Every build scans libraries and container images, and critical vulnerabilities get a 14-day fix deadline.

## Roadmap

Next quarter we will extend the engine to cover additional report families, add self-service scheduling for Finance and explore streaming delivery for near-real-time insight. Success will be measured by report timeliness, analyst satisfaction and the number of manual spreadsheets retired.
