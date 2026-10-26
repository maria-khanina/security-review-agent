# Writer brief: c065_card_token_vault

Author profile `table_lover`: Everything in tables (components, endpoints, data stores); prose is minimal and some tables are malformed.
- structure=tables_only, english=jargon_dense, hedging=none, terminology=consistent, staleness=none
- typical gaps: reasons and conditions that do not fit a table cell
- length 600-1300 words; typo rate 0.01; markdown breakage light; dangling references 1; TBD markers 0

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
- F1 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The client library is configured to ignore certificate errors after a failed deployment.
- F2 [ambiguity, low] Mention vault-db (PostgreSQL) naturally, but do NOT state: Which algorithms protect integrity and confidentiality. Wrap the sentence(s) that mention vault-db (PostgreSQL) (the place where that information should have been) in the F2 marker.
- F3 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Container images are never rescanned after the first build.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:AUTH-03|...⟧ Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- ⟦S:DATA-04|...⟧ Non-production environments must not contain real personal or card data.
- ⟦S:AUTHZ-01|...⟧ Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:DATA-02|...⟧ Personal data must have a defined retention period and be deleted when it expires or on verified request.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:DATA-05|...⟧ Reports and exports containing personal data must require authorization, be encrypted in storage and expire.
- ⟦S:AUTHZ-03|...⟧ Each service must use its own database account with the minimum grants and no shared administrative credentials.
- ⟦S:API-01|...⟧ All external inputs must be validated against a schema and rejected if invalid.
- ⟦S:LOG-04|...⟧ Access to centralized logs must be limited to authorized staff.
- ⟦S:API-04|...⟧ Error responses must not reveal stack traces, SQL or internal hostnames.
- ⟦S:CRYPTO-02|...⟧ Primary account numbers must never be stored in clear text and must be tokenized by the card token vault.
- ⟦S:CRYPTO-04|...⟧ Traffic between services and to data stores must be encrypted in transit.
- ⟦S:CRYPTO-06|...⟧ Encryption keys must be held in KMS, never stored with the data they protect, and rotated at least annually.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:NET-04|...⟧ Services calling third parties must have egress restricted to an approved allowlist.
- ⟦S:API-03|...⟧ Outbound and inbound webhook payloads must be signed and signatures verified.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:OPS-02|...⟧ Containers must run as a non-root user with a read-only root filesystem where possible.
- ⟦S:OPS-03|...⟧ Backups must be encrypted and restoration must be tested at least twice a year.
- ⟦S:SECRET-03|...⟧ Service credentials must be rotated at least every 90 days and immediately after suspected exposure.
- ⟦S:DATA-01|...⟧ Services must collect and store only the personal data needed for their purpose.

## Functional content (no security claims)
Aim for at least 600 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c065_card_token_vault/design_marked.md
