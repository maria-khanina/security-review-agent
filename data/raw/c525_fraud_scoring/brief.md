# Writer brief: c525_fraud_scoring

Author profile `copy_paste_veteran`: Built from an older design with find-and-replace; stale service names and sentences that contradict the new section.
- structure=clean_headings, english=native_fluent, hedging=none, terminology=aliases_drift, staleness=heavy_copy_paste
- typical gaps: which version of the auth scheme is current
- length 1400-2400 words; typo rate 0.0; markdown breakage light; dangling references 0; TBD markers 0

Service: Real-time risk scoring consuming payment events and writing decisions. (Meridian Pay, internal exposure, data: pii, internal)

Components:
- scoring-engine (service)
- payment-events (MSK) (message_queue)
- decisions-db (PostgreSQL) (database)
- scoring audit log group (log_pipeline)

Flows:
- payment-events (MSK) -> scoring-engine: payment events with customer attributes
- scoring-engine -> decisions-db (PostgreSQL): risk decisions
- scoring-engine -> scoring audit log group: audit records

Implementation (terraform) the document describes:
- kms `scoring_key`
- msk `payment_events`
- rds `decisions_db` (holds pii)
- sg `decisions_sg`
- loggroup `scoring_audit`
- iam `scoring_policy`

## Planted items
- F1 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Rollback is tested only for the main service and not for the jobs.
- F2 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The signing key is available to every developer.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:RES-01|...⟧ Personal data of customers in the EU must be stored and processed only in regions of the EU.
- ⟦S:RES-02|...⟧ Backups and replicas of personal data of customers in the EU should stay in regions of the EU as well.
- ⟦S:PIP-01|...⟧ Credentials of the delivery pipeline must be issued for each run and be valid for at most 1 hour.

## Functional content (no security claims)
Aim for at least 1400 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c525_fraud_scoring/design_marked.md
