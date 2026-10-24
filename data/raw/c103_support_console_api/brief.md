# Writer brief: c103_support_console_api

Author profile `table_lover`: Everything in tables (components, endpoints, data stores); prose is minimal and some tables are malformed.
- structure=tables_only, english=jargon_dense, hedging=none, terminology=consistent, staleness=none
- typical gaps: reasons and conditions that do not fit a table cell
- length 600-1300 words; typo rate 0.01; markdown breakage light; dangling references 0; TBD markers 0

Service: Back-office API for support agents to look up customers, reset second factors and issue goodwill credits. (Meridian Pay, admin exposure, data: pii, credentials)

Components:
- console-backend (service)
- console-db (PostgreSQL) (database)
- Keycloak (identity_provider)
- Support web console (client_app)

Flows:
- Support web console -> console-backend: customer lookups and account actions
- console-backend -> Keycloak: agent token validation
- console-backend -> console-db (PostgreSQL): customer profiles and agent action records

Implementation (openapi) the document describes:
- GET /v1/customers: Search customers
- GET /v1/customers/{customerId}: Retrieve a customer profile
- POST /v1/customers/{customerId}/second-factor-reset: Reset the second factor of a customer
- POST /v1/customers/{customerId}/credits: Issue a goodwill credit
- GET /v1/agent-actions: List actions taken by support agents
- POST /v1/customers/{customerId}/data-export: Export the data held about a customer

## Planted items
- F1 [violation, low] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Validation failures return the full internal exception text.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTH-03|...⟧ Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- ⟦S:AUTH-04|...⟧ Administrative and back-office access must require multi-factor authentication.
- ⟦S:AUTH-05|...⟧ Passwords must be stored only as salted hashes using argon2id or bcrypt and never in reversible form.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:CRYPTO-06|...⟧ Encryption keys must be held in KMS, never stored with the data they protect, and rotated at least annually.
- ⟦S:CRYPTO-07|...⟧ Services must validate TLS certificates and must not disable verification.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:NET-04|...⟧ Services calling third parties must have egress restricted to an approved allowlist.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:DATA-04|...⟧ Non-production environments must not contain real personal or card data.
- ⟦S:API-03|...⟧ Outbound and inbound webhook payloads must be signed and signatures verified.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- ⟦S:OPS-02|...⟧ Containers must run as a non-root user with a read-only root filesystem where possible.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:DATA-02|...⟧ Personal data must have a defined retention period and be deleted when it expires or on verified request.
- ⟦S:LOG-04|...⟧ Access to centralized logs must be limited to authorized staff.
- ⟦S:DATA-05|...⟧ Reports and exports containing personal data must require authorization, be encrypted in storage and expire.
- ⟦S:AUTHZ-01|...⟧ Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.
- ⟦S:API-01|...⟧ All external inputs must be validated against a schema and rejected if invalid.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.

## Functional content (no security claims)
Aim for at least 600 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.
Functional detail to describe for each endpoint:
- GET /v1/customers: request fields none; response fields id, full_name, email, phone_number, status
- GET /v1/customers/{customerId}: request fields none; response fields id, full_name, email, phone_number, status
- POST /v1/customers/{customerId}/second-factor-reset: request fields reason, ticket_id; response fields id, status
- POST /v1/customers/{customerId}/credits: request fields amount, currency, reason, ticket_id; response fields id, amount, currency, status
- GET /v1/agent-actions: request fields none; response fields id, agent_id, action, created_at
- POST /v1/customers/{customerId}/data-export: request fields format, reason; response fields id, status, expires_at

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c103_support_console_api/design_marked.md
