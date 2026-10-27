# Writer brief: c607_fraud_scoring

Author profile `migration_delta_writer`: Describes only what changes relative to the existing system and assumes the old behavior carries over.
- structure=delta_only, english=native_fluent, hedging=low, terminology=consistent, staleness=some_outdated
- typical gaps: security properties inherited from the old system
- length 700-1500 words; typo rate 0.01; markdown breakage light; dangling references 1; TBD markers 0

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
None. This is a clean case: no violation and no ambiguity.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:ARC-01|...⟧ Transaction records must be kept for 7 years and must be deleted within 90 days after that period ends.
- ⟦S:ARC-02|...⟧ Documents uploaded by customers must be deleted within 30 days after the account is closed.
- ⟦S:VUL-01|...⟧ Vulnerabilities rated critical must be fixed in production within 7 days after they are published.
- ⟦S:TST-01|...⟧ Production data must not be copied to test or development environments.
- ⟦S:TST-02|...⟧ Test accounts in production must be removed within 7 days after the test ends.
- ⟦S:EXP-02|...⟧ Exports of more than 1,000 customer records need the written approval of the data owner.
- ⟦S:INV-01|...⟧ Every service must have a named owner and a named deputy in the service register.
- ⟦S:INV-02|...⟧ The service register must list for each service the personal data that it processes and every third party that receives data from it.
- ⟦S:FRD-01|...⟧ Transactions above 10,000 EUR must be held for review by the fraud team before they are settled.
- ⟦S:MON-01|...⟧ Alerts of severity high must be acknowledged within 15 minutes.
- ⟦S:WHK-01|...⟧ Callbacks to endpoints of customers must be signed and must carry a timestamp that the receiver can check against replay.

## Functional content (no security claims)
Aim for at least 700 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c607_fraud_scoring/design_marked.md
