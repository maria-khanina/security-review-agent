# Reporting Export - design (two parts, merged)

> Part A written by Olga (finance engineering), Part B by Viktor (platform). Merged in a hurry before the review; the two parts use different names for the same things (see the glossary at the end, it is not complete).

## Part A - What we build (Olga)

The **Reporting Export** produces the scheduled settlement and transaction reports that Finance needs each night and at month end. Finance used to run these queries by hand on the main database. This is **slow, error-prone, and sometimes ran at the same time as the payments batch**, so we moved it to its own job.

### Pieces

- **export-job** - the scheduled job (night + month end). In my half I call it "the exporter".
- **reporting read replica (PostgreSQL)** - a copy of the main database that is read-only. The exporter reads from it.
- **exports bucket (S3)** - where the CSV files go. One file per report type and date range.
- **reporting private subnet** - the network segment where the pieces live.

### How a run goes

1. The scheduler starts the exporter at 02:00 (month end: 01:00).
2. The exporter reads the data for the requested report from the replica. Long date ranges are cut into chunks so the replica is not blocked.
3. It writes a CSV under a temporary name and renames it when it is complete, so *nobody ever sees half a file*.
4. A rerun with the same run id replaces the file; a failed run writes nothing and sends an alert to the Finance Engineering channel.

⟦F2|The export-job reads the settlement and transaction records for each report from the reporting read replica.⟧

### What Finance gets

⟦F3|The exports bucket is private and the analysts download the files through pre-signed URLs.⟧ File names have the report type, the range and the run id. Finance asked for one file per run; engineering would split above a million rows - not decided.

---

## Part B - Platform and security (Viktor)

Hi, I'm doing the infra half. In my part the exporter is "the job" and the replica is "the RO db" - sorry for the naming, Olga uses the other words.

**Infra.** Terraform declares the KMS key `export_key`, the bucket `exports_bucket`, the instance `reporting_ro_db`, the security group `reporting_sg`, the log group `export_audit` and the policy `export_job_policy`.

**Controls.** The platform team's standard statements apply, and for this service they read like this:

* ⟦S:AUTH-03|Access tokens expire within 15 minutes; refresh tokens are rotated on use.⟧
* ⟦S:AUTH-04|Administrative and back-office access requires multi-factor authentication.⟧
* ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧
* ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧
* ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
* ⟦S:CRYPTO-06|Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.⟧
* ⟦S:CRYPTO-07|Services validate TLS certificates and never disable verification.⟧
* ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧
* ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧
* ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧
* ⟦S:NET-04|Services that call third parties have their egress restricted to an approved allowlist.⟧
* ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧
* ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧
* ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧
* ⟦S:API-03|Callback payloads, outbound and inbound, are signed, and the signatures are verified.⟧
* ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧
* ⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧
* ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧

**Database password.** ⟦F1|Rotation of the database passwords is avoided because every rotation needs a restart of the job.⟧ The restart is the reason; nobody likes it but nobody wants to touch the month end run.

**Capacity.** The replica is sized for the month end run, which takes around forty minutes. The bucket grows by a few gigabytes a month. Lifecycle of the bucket was discussed, see the note from March (link not valid).

### Glossary (incomplete)

| Olga says | Viktor says |
|---|---|
| the exporter | the job / export-job |
| the replica | the RO db |
| Finance Engineering channel | #fin-eng |

Old design: "Export v1" in the previous wiki (page moved, link no longer works). The dashboards of v1 are still linked from the team page (link not valid either).
