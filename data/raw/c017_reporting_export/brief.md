# Writer brief: c017_reporting_export

Author profile `diagram_narrator`: Mostly an ASCII or mermaid diagram plus short captions; flows exist only as arrows between boxes.
- structure=diagram_narration, english=jargon_dense, hedging=none, terminology=consistent, staleness=none
- typical gaps: trust boundaries, credentials on arrows, protocols on arrows
- length 500-1100 words; typo rate 0.01; markdown breakage light; dangling references 0; TBD markers 0

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
- F1 [ambiguity, low] Mention exports bucket (S3) naturally, but do NOT state: How backups are protected and verified. Wrap the sentence(s) that mention exports bucket (S3) (the place where that information should have been) in the F1 marker.
- F2 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The database has a public endpoint so the partner's reporting tool can read from it.
- F3 [ambiguity, medium] Mention export-job naturally, but do NOT state: Where administrative endpoints are exposed and to whom. Wrap the sentence(s) that mention export-job (the place where that information should have been) in the F3 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:AUTH-04|...⟧ Administrative and back-office access must require multi-factor authentication.
- ⟦S:AUTHZ-02|...⟧ Internal users must receive only the roles required for their job and roles must be defined per service.
- ⟦S:AUTHZ-05|...⟧ Access rights to production systems must be reviewed at least quarterly.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:DATA-01|...⟧ Services must collect and store only the personal data needed for their purpose.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:DATA-05|...⟧ Reports and exports containing personal data must require authorization, be encrypted in storage and expire.
- ⟦S:NET-02|...⟧ Object storage buckets must block public access and be private by default.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.

## Functional content (no security claims)
Aim for at least 500 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c017_reporting_export/design_marked.md
