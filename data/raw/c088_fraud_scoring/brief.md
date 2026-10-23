# Writer brief: c088_fraud_scoring

Author profile `migration_delta_writer`: Describes only what changes relative to the existing system and assumes the old behavior carries over.
- structure=delta_only, english=native_fluent, hedging=low, terminology=consistent, staleness=some_outdated
- typical gaps: security properties inherited from the old system
- length 700-1500 words; typo rate 0.0; markdown breakage none; dangling references 1; TBD markers 0

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
- F1 [drift, high] State as plain fact, adapted to this service: The database sits in private subnets with no public endpoint. Wrap the sentence(s) in the F1 marker.
- F2 [ambiguity, low] Mention scoring-engine naturally, but do NOT state: What data is shared with the vendor and under what agreement. Wrap the sentence(s) that mention scoring-engine (the place where that information should have been) in the F2 marker.
- F3 [ambiguity, low] Mention scoring-engine naturally, but do NOT state: How the service obtains its secrets at runtime. Wrap the sentence(s) that mention scoring-engine (the place where that information should have been) in the F3 marker.
- F4 [ambiguity, low] Mention decisions-db (PostgreSQL) naturally, but do NOT state: Which database identity each service uses and its grants. Wrap the sentence(s) that mention decisions-db (PostgreSQL) (the place where that information should have been) in the F4 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:DATA-02|...⟧ Personal data must have a defined retention period and be deleted when it expires or on verified request.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.

## Functional content (no security claims)
Aim for at least 700 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c088_fraud_scoring/design_marked.md
