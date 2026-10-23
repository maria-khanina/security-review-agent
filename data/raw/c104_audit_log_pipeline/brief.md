# Writer brief: c104_audit_log_pipeline

Author profile `esl_engineer`: Competent engineer writing in a second language; missing articles, literal translations of idioms, odd word order.
- structure=clean_headings, english=esl_calques, hedging=low, terminology=consistent, staleness=none
- typical gaps: negations and obligations phrased ambiguously, e.g. "should not be only encrypted"
- length 1000-1800 words; typo rate 0.03; markdown breakage light; dangling references 1; TBD markers 0

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
- F1 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Audit logs are stored for 30 days on the same system that writes them.
- F2 [ambiguity, low] Mention pipeline log group naturally, but do NOT state: Who can read the logs. Wrap the sentence(s) that mention pipeline log group (the place where that information should have been) in the F2 marker.
- F3 [drift, high] State as plain fact, adapted to this service: The bucket is private and accessed through pre-signed URLs. Wrap the sentence(s) in the F3 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:AUTHZ-02|...⟧ Internal users must receive only the roles required for their job and roles must be defined per service.
- ⟦S:AUTHZ-05|...⟧ Access rights to production systems must be reviewed at least quarterly.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:DATA-01|...⟧ Services must collect and store only the personal data needed for their purpose.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.

## Functional content (no security claims)
Aim for at least 1000 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c104_audit_log_pipeline/design_marked.md
