# Writer brief: c077_card_token_vault

Author profile `tribal_knowledge_staff`: Overcommitted senior engineer; dense jargon and abbreviations, assumes the reader knows the platform.
- structure=bullets_only, english=jargon_dense, hedging=none, terminology=consistent, staleness=none
- typical gaps: anything covered by "the usual platform setup"
- length 500-1000 words; typo rate 0.0; markdown breakage light; dangling references 1; TBD markers 2

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
- F1 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Internal endpoints are protected only by obscure URL paths.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:API-01|...⟧ All external inputs must be validated against a schema and rejected if invalid.
- ⟦S:AUTHZ-02|...⟧ Internal users must receive only the roles required for their job and roles must be defined per service.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:AUTHZ-05|...⟧ Access rights to production systems must be reviewed at least quarterly.
- ⟦S:CRYPTO-02|...⟧ Primary account numbers must never be stored in clear text and must be tokenized by the card token vault.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:DATA-05|...⟧ Reports and exports containing personal data must require authorization, be encrypted in storage and expire.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:AUTHZ-01|...⟧ Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.
- ⟦S:CRYPTO-04|...⟧ Traffic between services and to data stores must be encrypted in transit.
- ⟦S:AUTH-03|...⟧ Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- ⟦S:OPS-03|...⟧ Backups must be encrypted and restoration must be tested at least twice a year.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- ⟦S:DATA-02|...⟧ Personal data must have a defined retention period and be deleted when it expires or on verified request.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:CRYPTO-06|...⟧ Encryption keys must be held in KMS, never stored with the data they protect, and rotated at least annually.

## Functional content (no security claims)
Aim for at least 500 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c077_card_token_vault/design_marked.md
