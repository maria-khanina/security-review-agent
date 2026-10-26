# data warehouse sync - design meeting (notes)

Attendees: Petra, Jonas, Amir, Lena (joined late)
Notes: Amir
Old doc: "analytics-feed" page on the previous wiki (link dead)

## context

Goal: copy the tables the analytics vendor needs from the production replica into a staging bucket every night, so the vendor can load them into their warehouse. Replaces the old CSV mails that Jonas sent by hand. The thing that does the copy is the sync-job (a.k.a. "the feeder" in the old doc). It reads from the analytics read replica (PostgreSQL), writes extract files to the staging bucket (S3), the vendor picks up the files from there. Terraform names: warehouse_key, staging_bucket, analytics_replica, analytics_sg, sync_audit, sync_job_policy.

## discussion

**What goes into the extracts.** The sync-job copies the selected tables from the analytics read replica into one extract file per table. Which columns exactly - Petra says the vendor "will tell us what they need", Jonas thinks we start with everything and trim later (TBD, nobody decided).

**Vendor.** The extract files are sent to the analytics vendor under a verbal agreement, and the written contract will follow once the pilot is over. Lena (late) asked if legal knows, nobody could say (TBD, Amir to ask legal).

**Download.** Vendor needs to pull the files without us creating links every night. The reports are served from a publicly readable bucket, so that nobody has to generate download links. Petra not happy, Jonas says it is only for the pilot (TBD).

Access tokens live for at most 15 minutes, and every refresh token is replaced when it is used.
Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
Every build scans libraries and container images, and critical vulnerabilities get a 14-day fix deadline.

**Access and platform.** Short list from the platform checklist, nobody objected:
- Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.
- The audit trail is tamper-evident, and we keep it for no less than twelve months.
- Backup encryption is on, and we test restoring from backup at least every six months.
- Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.
- Internal users are given the minimum set of roles for their job, and roles are defined service by service.
- Access lists are reviewed only before an external audit.
- The databases and object stores that hold PII use AES-256 encryption at rest.
- Log access is granted to whole teams and is never removed.
- Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.
- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- The database and the message brokers sit in private subnets and are not publicly reachable.
- KMS holds the keys, the data stores only keep ciphertext, and key rotation happens at least yearly.
- Admin and debug endpoints are reachable only from the internal network, not from the public internet.
- On boot, the service pulls its credentials from the approved secret store.
- Authentication failures, privilege changes and access to sensitive data are written to the logs.
- All queries use bound parameters instead of string concatenation.

**Schedule.** Run at 03:00, takes about 20 min for the current table set. If a run fails nothing is overwritten and the vendor keeps yesterday's files. Alert goes to #data-eng (weekend routing TBD).

## action items

- Amir: ask legal about the vendor contract (TBD)
- Jonas: list of columns with Petra (TBD)
- Petra: decide with Jonas if the bucket stays as it is after the pilot (TBD)
- Lena: nothing, was late
