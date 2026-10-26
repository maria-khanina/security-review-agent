# Writer brief: c529_reporting_export

Author profile `tribal_knowledge_staff`: Overcommitted senior engineer; dense jargon and abbreviations, assumes the reader knows the platform.
- structure=bullets_only, english=jargon_dense, hedging=none, terminology=consistent, staleness=none
- typical gaps: anything covered by "the usual platform setup"
- length 500-1000 words; typo rate 0.0; markdown breakage none; dangling references 0; TBD markers 2

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
- F1 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The database runs in a cheaper region outside the EU.
- F2 [ambiguity, medium] Mention export-job naturally, but do NOT state: How the pipeline gets its credentials and how long they are valid. Wrap the sentence(s) that mention export-job (the place where that information should have been) in the F2 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:RES-02|...⟧ Backups and replicas of personal data of customers in the EU should stay in regions of the EU as well.
- ⟦S:PIP-02|...⟧ Build artifacts must be signed, and the signature must be verified before deployment.
- ⟦S:CHG-02|...⟧ Every change to production must have a rollback plan that has been tested in a pre-production environment.
- ⟦S:OBS-01|...⟧ Traces and metrics must not contain personal data or card data.
- ⟦S:OBS-02|...⟧ Every service must publish its health check and error rates to the shared dashboard every minute.
- ⟦S:PRV-03|...⟧ Personal data must be used only for purposes listed in the privacy notice shown to customers at sign-up.

## Functional content (no security claims)
Aim for at least 500 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c529_reporting_export/design_marked.md
