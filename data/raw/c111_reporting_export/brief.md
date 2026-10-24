# Writer brief: c111_reporting_export

Author profile `tribal_knowledge_staff`: Overcommitted senior engineer; dense jargon and abbreviations, assumes the reader knows the platform.
- structure=bullets_only, english=jargon_dense, hedging=none, terminology=consistent, staleness=none
- typical gaps: anything covered by "the usual platform setup"
- length 500-1000 words; typo rate 0.01; markdown breakage none; dangling references 0; TBD markers 0

Service: Scheduled exports of settlement and transaction reports to object storage for finance. (Meridian Pay, admin exposure, data: pii, internal)

Components:
- export-job (service)
- exports bucket (S3) (object_storage)
- reporting read replica (PostgreSQL) (database)
- reporting private subnet (network)

Flows:
- export-job -> reporting read replica (PostgreSQL): settlement and transaction queries
- export-job -> exports bucket (S3): generated report files
- Finance analysts -> exports bucket (S3): report downloads

Implementation (terraform) the document describes:
- kms `export_key`
- s3 `exports_bucket` (holds pii)
- rds `reporting_ro_db` (holds pii)
- sg `reporting_sg`
- loggroup `export_audit`
- iam `export_job_policy`

## Planted items
- F1 [ambiguity, medium] Mention reporting read replica (PostgreSQL) naturally, but do NOT state: Network placement of the database or broker. Wrap the sentence(s) that mention reporting read replica (PostgreSQL) (the place where that information should have been) in the F1 marker.
- F2 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The container user is not set, so processes run as root.
- F3 [ambiguity, medium] Mention reporting read replica (PostgreSQL) naturally, but do NOT state: Which database identity each service uses and its grants. Wrap the sentence(s) that mention reporting read replica (PostgreSQL) (the place where that information should have been) in the F3 marker.
- F4 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Error logs include the authorization header and request payload to help support.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:NET-02|...⟧ Object storage buckets must block public access and be private by default.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:DATA-02|...⟧ Personal data must have a defined retention period and be deleted when it expires or on verified request.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.

## Functional content (no security claims)
Aim for at least 500 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c111_reporting_export/design_marked.md
