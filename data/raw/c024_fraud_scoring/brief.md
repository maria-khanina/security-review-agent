# Writer brief: c024_fraud_scoring

Author profile `junior_tutorial`: Explains basics at length and mixes up concepts such as hashing, encryption and encoding, or JWT and sessions.
- structure=clean_headings, english=junior_tutorial, hedging=low, terminology=wrong_terms, staleness=none
- typical gaps: correct choice of primitives
- length 1500-2600 words; typo rate 0.01; markdown breakage none; dangling references 0; TBD markers 0

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
- F1 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): To simplify failover tests the database is reachable from outside the VPC.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:AUTH-03|...⟧ Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- ⟦S:CRYPTO-04|...⟧ Traffic between services and to data stores must be encrypted in transit.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:CRYPTO-07|...⟧ Services must validate TLS certificates and must not disable verification.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:AUTHZ-03|...⟧ Each service must use its own database account with the minimum grants and no shared administrative credentials.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:DATA-04|...⟧ Non-production environments must not contain real personal or card data.
- ⟦S:CRYPTO-06|...⟧ Encryption keys must be held in KMS, never stored with the data they protect, and rotated at least annually.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:NET-04|...⟧ Services calling third parties must have egress restricted to an approved allowlist.
- ⟦S:LOG-04|...⟧ Access to centralized logs must be limited to authorized staff.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:API-03|...⟧ Outbound and inbound webhook payloads must be signed and signatures verified.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- ⟦S:OPS-02|...⟧ Containers must run as a non-root user with a read-only root filesystem where possible.
- ⟦S:OPS-03|...⟧ Backups must be encrypted and restoration must be tested at least twice a year.
- ⟦S:AUTHZ-02|...⟧ Internal users must receive only the roles required for their job and roles must be defined per service.
- ⟦S:SECRET-03|...⟧ Service credentials must be rotated at least every 90 days and immediately after suspected exposure.
- ⟦S:LOG-03|...⟧ Audit logs must be tamper-evident and retained for at least one year.

## Functional content (no security claims)
Aim for at least 1500 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c024_fraud_scoring/design_marked.md
