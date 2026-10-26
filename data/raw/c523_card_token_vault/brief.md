# Writer brief: c523_card_token_vault

Author profile `compliance_voice`: Legalistic language citing standards and "in accordance with company policy" without saying what is actually done.
- structure=clean_headings, english=native_fluent, hedging=none, terminology=consistent, staleness=none
- typical gaps: concrete mechanism behind every claimed compliance
- length 1200-2200 words; typo rate 0.0; markdown breakage none; dangling references 0; TBD markers 0

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
- F1 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Debug traces with full payloads are switched on in production for a few services.
- F2 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Engineers deploy their own changes to production when they are confident.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:PIP-01|...⟧ Credentials of the delivery pipeline must be issued for each run and be valid for at most 1 hour.
- ⟦S:PIP-02|...⟧ Build artifacts must be signed, and the signature must be verified before deployment.
- ⟦S:CHG-02|...⟧ Every change to production must have a rollback plan that has been tested in a pre-production environment.
- ⟦S:OBS-02|...⟧ Every service must publish its health check and error rates to the shared dashboard every minute.
- ⟦S:PRV-03|...⟧ Personal data must be used only for purposes listed in the privacy notice shown to customers at sign-up.

## Functional content (no security claims)
Aim for at least 1200 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c523_card_token_vault/design_marked.md
