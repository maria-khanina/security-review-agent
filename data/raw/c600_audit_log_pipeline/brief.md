# Writer brief: c600_audit_log_pipeline

Author profile `methodical_architect`: Thorough and tidy, but works at a high level of abstraction and skips operational details.
- structure=clean_headings, english=native_fluent, hedging=low, terminology=consistent, staleness=none
- typical gaps: secret rotation, key ownership, who can query the database directly, logging of sensitive fields
- length 1800-2600 words; typo rate 0.0; markdown breakage none; dangling references 0; TBD markers 2

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
None. This is a clean case: no violation and no ambiguity.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:ARC-01|...⟧ Transaction records must be kept for 7 years and must be deleted within 90 days after that period ends.
- ⟦S:VUL-01|...⟧ Vulnerabilities rated critical must be fixed in production within 7 days after they are published.
- ⟦S:VUL-02|...⟧ Third-party components must not be more than two major versions behind the latest release, and the service register must show the version of each.
- ⟦S:TST-01|...⟧ Production data must not be copied to test or development environments.
- ⟦S:TST-02|...⟧ Test accounts in production must be removed within 7 days after the test ends.
- ⟦S:INV-01|...⟧ Every service must have a named owner and a named deputy in the service register.
- ⟦S:MON-01|...⟧ Alerts of severity high must be acknowledged within 15 minutes.

## Functional content (no security claims)
Aim for at least 1800 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c600_audit_log_pipeline/design_marked.md
