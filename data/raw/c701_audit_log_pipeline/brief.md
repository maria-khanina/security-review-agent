# Writer brief: c701_audit_log_pipeline

Author profile `meeting_notes`: Written as decisions and open questions after a design meeting; some decisions are reversed later in the same doc.
- structure=meeting_notes, english=native_sloppy, hedging=high, terminology=aliases_drift, staleness=none
- typical gaps: final outcome of open questions
- length 700-1400 words; typo rate 0.03; markdown breakage light; dangling references 0; TBD markers 5

Service: Collects audit events from all services and keeps them in a tamper-evident archive. (Meridian Pay, internal exposure, data: logs, pii)

Components:
- audit-collector (service)
- audit-stream (MSK) (message_queue)
- pipeline log group (log_pipeline)
- audit archive (S3) (object_storage)

Flows:
- Platform services -> audit-collector: audit events
- audit-collector -> audit-stream (MSK): normalized audit events
- audit-stream (MSK) -> audit archive (S3): archived audit batches
- audit-collector -> pipeline log group: collector operational logs

Implementation (terraform) the document describes:
- kms `audit_key`
- msk `audit_stream`
- s3 `audit_archive` (holds logs)
- loggroup `pipeline_audit`
- backup_vault `audit_backups`
- iam `pipeline_policy`

## Planted items
- F1 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Nobody knows which account a job uses because it was set up years ago.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:VER-01|...⟧ A replaced version of an API must be kept for 12 months, and its removal must be announced 90 days in advance.
- ⟦S:VER-02|...⟧ Breaking changes of an API must be released only as a new version of the API.
- ⟦S:MSG-02|...⟧ Messages in queues must be deleted after they are processed.

## Functional content (no security claims)
Aim for at least 700 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c701_audit_log_pipeline/design_marked.md
