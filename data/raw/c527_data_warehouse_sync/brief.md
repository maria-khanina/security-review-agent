# Writer brief: c527_data_warehouse_sync

Author profile `meeting_notes`: Written as decisions and open questions after a design meeting; some decisions are reversed later in the same doc.
- structure=meeting_notes, english=native_sloppy, hedging=high, terminology=aliases_drift, staleness=none
- typical gaps: final outcome of open questions
- length 700-1400 words; typo rate 0.01; markdown breakage light; dangling references 0; TBD markers 2

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
- F1 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Traces record the full request including the name and the email of the customer.
- F2 [ambiguity, medium] Mention analytics read replica (PostgreSQL) naturally, but do NOT state: In which region the personal data of EU customers is stored and processed. Wrap the sentence(s) that mention analytics read replica (PostgreSQL) (the place where that information should have been) in the F2 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:RES-02|...⟧ Backups and replicas of personal data of customers in the EU should stay in regions of the EU as well.
- ⟦S:CHG-02|...⟧ Every change to production must have a rollback plan that has been tested in a pre-production environment.
- ⟦S:PIP-01|...⟧ Credentials of the delivery pipeline must be issued for each run and be valid for at most 1 hour.

## Functional content (no security claims)
Aim for at least 700 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c527_data_warehouse_sync/design_marked.md
