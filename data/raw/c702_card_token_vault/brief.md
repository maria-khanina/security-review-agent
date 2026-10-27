# Writer brief: c702_card_token_vault

Author profile `optimistic_roadmapper`: Describes planned features in present tense; future and current state are blurred.
- structure=clean_headings, english=native_fluent, hedging=low, terminology=consistent, staleness=none
- typical gaps: which controls exist today
- length 1200-2200 words; typo rate 0.01; markdown breakage none; dangling references 1; TBD markers 2

Service: PCI-scoped store that tokenizes primary account numbers for other services. (Meridian Pay, internal exposure, data: card_data)

Components:
- tokenization-service (service)
- vault-db (PostgreSQL) (database)
- Vault and KMS (secret_store)
- vault private subnet (network)

Flows:
- Payment services -> tokenization-service: primary account numbers to tokenize and tokens to detokenize
- tokenization-service -> vault-db (PostgreSQL): encrypted card data
- tokenization-service -> Vault and KMS: data encryption key requests

Implementation (terraform) the document describes:
- kms `vault_key`
- rds `vault_db` (holds card_data)
- sg `vault_db_sg`
- loggroup `vault_audit`
- backup_vault `vault_backups`
- iam `vault_service_policy`

## Planted items
- F1 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Processed messages are archived in a bucket without deletion.
- F2 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Merchants can test with real card numbers in the sandbox.
- F3 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Only the payment endpoint is idempotent, transfers are not.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:REC-02|...⟧ Differences found in a reconciliation must be resolved within 5 working days.
- ⟦S:VER-01|...⟧ A replaced version of an API must be kept for 12 months, and its removal must be announced 90 days in advance.
- ⟦S:VER-02|...⟧ Breaking changes of an API must be released only as a new version of the API.
- ⟦S:JOB-01|...⟧ Scheduled jobs must run with their own service account that cannot log in interactively.
- ⟦S:SUP-01|...⟧ Support agents must see card numbers and document numbers only in masked form.

## Functional content (no security claims)
Aim for at least 1200 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c702_card_token_vault/design_marked.md
