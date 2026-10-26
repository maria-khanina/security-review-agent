# Writer brief: c023_fraud_scoring

Author profile `migration_delta_writer`: Describes only what changes relative to the existing system and assumes the old behavior carries over.
- structure=delta_only, english=native_fluent, hedging=low, terminology=consistent, staleness=some_outdated
- typical gaps: security properties inherited from the old system
- length 700-1500 words; typo rate 0.01; markdown breakage none; dangling references 0; TBD markers 0

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
- F1 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): A raw SQL fragment from the query string is appended to the report query.
- F2 [ambiguity, low] Mention decisions-db (PostgreSQL) naturally, but do NOT state: How long personal data is kept and how it is deleted. Wrap the sentence(s) that mention decisions-db (PostgreSQL) (the place where that information should have been) in the F2 marker.
- F3 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Only HTTP access logs from the load balancer are kept.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:CRYPTO-04|...⟧ Traffic between services and to data stores must be encrypted in transit.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:OPS-02|...⟧ Containers must run as a non-root user with a read-only root filesystem where possible.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:AUTHZ-03|...⟧ Each service must use its own database account with the minimum grants and no shared administrative credentials.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- ⟦S:AUTH-03|...⟧ Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- ⟦S:OPS-03|...⟧ Backups must be encrypted and restoration must be tested at least twice a year.
- ⟦S:LOG-03|...⟧ Audit logs must be tamper-evident and retained for at least one year.

## Functional content (no security claims)
Aim for at least 700 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c023_fraud_scoring/design_marked.md
