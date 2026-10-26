# Writer brief: c069_card_token_vault

Author profile `meeting_notes`: Written as decisions and open questions after a design meeting; some decisions are reversed later in the same doc.
- structure=meeting_notes, english=native_sloppy, hedging=high, terminology=aliases_drift, staleness=none
- typical gaps: final outcome of open questions
- length 700-1400 words; typo rate 0.03; markdown breakage none; dangling references 1; TBD markers 2

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
None. This is a clean case: no violation and no ambiguity.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:AUTH-03|...⟧ Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:CRYPTO-02|...⟧ Primary account numbers must never be stored in clear text and must be tokenized by the card token vault.
- ⟦S:CRYPTO-04|...⟧ Traffic between services and to data stores must be encrypted in transit.
- ⟦S:CRYPTO-07|...⟧ Services must validate TLS certificates and must not disable verification.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:CRYPTO-06|...⟧ Encryption keys must be held in KMS, never stored with the data they protect, and rotated at least annually.
- ⟦S:API-04|...⟧ Error responses must not reveal stack traces, SQL or internal hostnames.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:AUTHZ-01|...⟧ Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:NET-04|...⟧ Services calling third parties must have egress restricted to an approved allowlist.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:DATA-04|...⟧ Non-production environments must not contain real personal or card data.
- ⟦S:API-03|...⟧ Outbound and inbound webhook payloads must be signed and signatures verified.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- ⟦S:OPS-02|...⟧ Containers must run as a non-root user with a read-only root filesystem where possible.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:OPS-03|...⟧ Backups must be encrypted and restoration must be tested at least twice a year.
- ⟦S:AUTHZ-02|...⟧ Internal users must receive only the roles required for their job and roles must be defined per service.
- ⟦S:DATA-01|...⟧ Services must collect and store only the personal data needed for their purpose.

## Functional content (no security claims)
Aim for at least 700 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c069_card_token_vault/design_marked.md
