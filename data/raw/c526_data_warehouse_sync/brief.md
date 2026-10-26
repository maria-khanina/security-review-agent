# Writer brief: c526_data_warehouse_sync

Author profile `esl_engineer`: Competent engineer writing in a second language; missing articles, literal translations of idioms, odd word order.
- structure=clean_headings, english=esl_calques, hedging=low, terminology=consistent, staleness=none
- typical gaps: negations and obligations phrased ambiguously, e.g. "should not be only encrypted"
- length 1000-1800 words; typo rate 0.01; markdown breakage light; dangling references 0; TBD markers 0

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
- F1 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The service deletes the customer record but leaves copies in reports and exports.
- F2 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Backups are copied to a bucket outside the EU for cheaper storage.
- F3 [ambiguity, low] Mention sync-job naturally, but do NOT state: Whether build artifacts are signed and checked before deployment. Wrap the sentence(s) that mention sync-job (the place where that information should have been) in the F3 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:RES-01|...⟧ Personal data of customers in the EU must be stored and processed only in regions of the EU.
- ⟦S:PIP-01|...⟧ Credentials of the delivery pipeline must be issued for each run and be valid for at most 1 hour.
- ⟦S:CHG-02|...⟧ Every change to production must have a rollback plan that has been tested in a pre-production environment.
- ⟦S:OBS-02|...⟧ Every service must publish its health check and error rates to the shared dashboard every minute.
- ⟦S:CHG-01|...⟧ Every change to production must be reviewed by a second engineer before it is deployed.

## Functional content (no security claims)
Aim for at least 1000 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c526_data_warehouse_sync/design_marked.md
