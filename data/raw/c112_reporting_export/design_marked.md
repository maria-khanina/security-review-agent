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

* ⟦S:AUTH-03|Access token lifetime is capped at 15 minutes, and using a refresh token rotates it.⟧
* ⟦S:AUTH-04|Back-office and administrative accounts cannot log in with a password alone, because MFA is enforced.⟧
* ⟦S:AUTHZ-04|Admin and debug endpoints are reachable only from the internal network, not from the public internet.⟧
* ⟦S:CRYPTO-01|The databases and object stores that hold PII use AES-256 encryption at rest.⟧
* ⟦S:CRYPTO-05|The approved algorithm list is followed, and MD5, SHA-1, DES, 3DES and ECB mode are prohibited in this service.⟧
* ⟦S:CRYPTO-06|Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year.⟧
* ⟦S:CRYPTO-07|TLS certificate verification is enabled in all clients, with no option to disable it.⟧
* ⟦S:SECRET-01|Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.⟧
* ⟦S:SECRET-02|Runtime secrets are read from the secret store when the service starts.⟧
* ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧
* ⟦S:NET-04|Third-party calls leave through an egress allowlist, not through open outbound access.⟧
* ⟦S:LOG-01|The audit trail includes authentication failures, privilege changes and sensitive-data access.⟧
* ⟦S:DATA-03|Third parties receive only the fields they need, and only if an approved data processing agreement covers them.⟧
* ⟦S:DATA-04|Non-production environments contain no real personal or card data.⟧
* ⟦S:API-03|Callback payloads, outbound and inbound, are signed, and the signatures are verified.⟧
* ⟦S:API-05|We use parameterized queries only, with no SQL built from user input by string concatenation.⟧
* ⟦S:OPS-01|Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less.⟧
* ⟦S:OPS-02|No container runs as root, and the root filesystem is read-only wherever possible.⟧

**Database password.** ⟦F1|Rotation of the database passwords is avoided because every rotation needs a restart of the job.⟧ The restart is the reason; nobody likes it but nobody wants to touch the month end run.

**Capacity.** The replica is sized for the month end run, which takes around forty minutes. The bucket grows by a few gigabytes a month. Lifecycle of the bucket was discussed, see the note from March (link not valid).

### Glossary (incomplete)

| Olga says | Viktor says |
|---|---|
| the exporter | the job / export-job |
| the replica | the RO db |
| Finance Engineering channel | #fin-eng |

Old design: "Export v1" in the previous wiki (page moved, link no longer works). The dashboards of v1 are still linked from the team page (link not valid either).
