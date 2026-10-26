# Writer brief: c122_data_warehouse_sync

Author profile `table_lover`: Everything in tables (components, endpoints, data stores); prose is minimal and some tables are malformed.
- structure=tables_only, english=jargon_dense, hedging=none, terminology=consistent, staleness=none
- typical gaps: reasons and conditions that do not fit a table cell
- length 600-1300 words; typo rate 0.0; markdown breakage heavy; dangling references 0; TBD markers 0

Service: Nightly copy of selected production tables into a staging bucket that an analytics vendor reads. (Meridian Pay, internal exposure, data: pii, internal)

Components:
- sync-job (service)
- analytics read replica (PostgreSQL) (database)
- staging bucket (S3) (object_storage)
- Analytics vendor (third_party)

Flows:
- sync-job -> analytics read replica (PostgreSQL): table extracts
- sync-job -> staging bucket (S3): extract files
- Analytics vendor -> staging bucket (S3): extract downloads

Implementation (terraform) the document describes:
- kms `warehouse_key`
- s3 `staging_bucket` (holds pii)
- rds `analytics_replica` (holds pii)
- sg `analytics_sg`
- loggroup `sync_audit`
- iam `sync_job_policy`

## Planted items
- F1 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The profile table keeps every attribute the mobile app can send.
- F2 [ambiguity, low] Mention sync-job naturally, but do NOT state: Which security events are logged. Wrap the sentence(s) that mention sync-job (the place where that information should have been) in the F2 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:AUTHZ-02|...⟧ Internal users must receive only the roles required for their job and roles must be defined per service.
- ⟦S:AUTHZ-05|...⟧ Access rights to production systems must be reviewed at least quarterly.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:NET-02|...⟧ Object storage buckets must block public access and be private by default.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:DATA-05|...⟧ Reports and exports containing personal data must require authorization, be encrypted in storage and expire.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:LOG-04|...⟧ Access to centralized logs must be limited to authorized staff.
- ⟦S:CRYPTO-04|...⟧ Traffic between services and to data stores must be encrypted in transit.
- ⟦S:AUTH-03|...⟧ Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- ⟦S:DATA-02|...⟧ Personal data must have a defined retention period and be deleted when it expires or on verified request.
- ⟦S:LOG-03|...⟧ Audit logs must be tamper-evident and retained for at least one year.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:CRYPTO-06|...⟧ Encryption keys must be held in KMS, never stored with the data they protect, and rotated at least annually.

## Functional content (no security claims)
Aim for at least 600 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c122_data_warehouse_sync/design_marked.md
