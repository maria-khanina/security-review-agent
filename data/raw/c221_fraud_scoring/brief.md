# Writer brief: c221_fraud_scoring

Author profile `buzzword_pm`: Business framing, security stated as adjectives ("enterprise-grade", "secure by design") with no mechanisms.
- structure=clean_headings, english=native_fluent, hedging=none, terminology=wrong_terms, staleness=none
- typical gaps: every concrete control, algorithms, token lifetimes, network boundaries
- length 900-1600 words; typo rate 0.0; markdown breakage none; dangling references 0; TBD markers 0

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
- F1 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The alert rule runs once a day.
- F2 [ambiguity, low] Mention decisions-db (PostgreSQL) naturally, but do NOT state: Whether point-in-time recovery is enabled for the databases and for how long. Wrap the sentence(s) that mention decisions-db (PostgreSQL) (the place where that information should have been) in the F2 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.

## Functional content (no security claims)
Aim for at least 900 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c221_fraud_scoring/design_marked.md
