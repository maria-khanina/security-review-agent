# Writer brief: c031_fraud_scoring

Author profile `sprint_rusher`: Terse bullet fragments, many TBD markers, sections left as headings with one line.
- structure=bullets_only, english=native_sloppy, hedging=low, terminology=aliases_drift, staleness=none
- typical gaps: auth between internal services, encryption at rest, data retention, error handling
- length 400-900 words; typo rate 0.01; markdown breakage none; dangling references 0; TBD markers 0

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
- F1 [violation, medium] The design must stay silent about: Admin ports closed to the internet. The issue exists only in the implementation. Do not mark any text for F1.
- F2 [ambiguity, low] Mention decisions-db (PostgreSQL) naturally, but do NOT state: How long personal data is kept and how it is deleted. Wrap the sentence(s) that mention decisions-db (PostgreSQL) (the place where that information should have been) in the F2 marker.
- F3 [violation, medium] State, as the author naturally would and believing it acceptable: All services connect to the database with the shared master user.
- F4 [ambiguity, low] Mention scoring-engine naturally, but do NOT state: How the service obtains its secrets at runtime. Wrap the sentence(s) that mention scoring-engine (the place where that information should have been) in the F4 marker.
- F5 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Filters are built by joining user-provided strings because the ORM could not express them.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:CRYPTO-04|...⟧ Traffic between services and to data stores must be encrypted in transit.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:OPS-02|...⟧ Containers must run as a non-root user with a read-only root filesystem where possible.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- ⟦S:AUTH-03|...⟧ Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- ⟦S:LOG-03|...⟧ Audit logs must be tamper-evident and retained for at least one year.
- ⟦S:OPS-03|...⟧ Backups must be encrypted and restoration must be tested at least twice a year.

## Functional content (no security claims)
Aim for at least 400 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c031_fraud_scoring/design_marked.md
