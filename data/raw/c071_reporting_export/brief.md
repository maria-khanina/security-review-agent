# Writer brief: c071_reporting_export

Author profile `buzzword_pm`: Business framing, security stated as adjectives ("enterprise-grade", "secure by design") with no mechanisms.
- structure=clean_headings, english=native_fluent, hedging=none, terminology=wrong_terms, staleness=none
- typical gaps: every concrete control, algorithms, token lifetimes, network boundaries
- length 900-1600 words; typo rate 0.01; markdown breakage light; dangling references 0; TBD markers 0

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
- F1 [ambiguity, medium] Mention exports bucket (S3) naturally, but do NOT state: Who can read objects in the bucket. Wrap the sentence(s) that mention exports bucket (S3) (the place where that information should have been) in the F1 marker.
- F2 [ambiguity, medium] Mention export-job naturally, but do NOT state: Where administrative endpoints are exposed and to whom. Wrap the sentence(s) that mention export-job (the place where that information should have been) in the F2 marker.
- F3 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Sort and filter parameters are inserted directly into the SQL text.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:OPS-02|...⟧ Containers must run as a non-root user with a read-only root filesystem where possible.
- ⟦S:DATA-02|...⟧ Personal data must have a defined retention period and be deleted when it expires or on verified request.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- ⟦S:AUTHZ-03|...⟧ Each service must use its own database account with the minimum grants and no shared administrative credentials.

## Functional content (no security claims)
Aim for at least 900 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c071_reporting_export/design_marked.md
