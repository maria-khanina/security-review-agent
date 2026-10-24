# Writer brief: c121_data_warehouse_sync

Author profile `esl_engineer`: Competent engineer writing in a second language; missing articles, literal translations of idioms, odd word order.
- structure=clean_headings, english=esl_calques, hedging=low, terminology=consistent, staleness=none
- typical gaps: negations and obligations phrased ambiguously, e.g. "should not be only encrypted"
- length 1000-1800 words; typo rate 0.03; markdown breakage light; dangling references 0; TBD markers 2

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
- F1 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): TLS between components was disabled during load tests and never turned back on.
- F2 [ambiguity, medium] Mention analytics read replica (PostgreSQL) naturally, but do NOT state: Network placement of the database or broker. Wrap the sentence(s) that mention analytics read replica (PostgreSQL) (the place where that information should have been) in the F2 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:OPS-02|...⟧ Containers must run as a non-root user with a read-only root filesystem where possible.
- ⟦S:NET-02|...⟧ Object storage buckets must block public access and be private by default.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:DATA-02|...⟧ Personal data must have a defined retention period and be deleted when it expires or on verified request.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.

## Functional content (no security claims)
Aim for at least 1000 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c121_data_warehouse_sync/design_marked.md
