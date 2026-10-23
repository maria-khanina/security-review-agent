# Writer brief: c015_merchant_portal_api

Author profile `security_champion`: Long dedicated security section with many named controls, but some are aspirational and terms are used loosely.
- structure=clean_headings, english=native_fluent, hedging=none, terminology=wrong_terms, staleness=some_outdated
- typical gaps: implementation status of the controls it lists
- length 1800-2600 words; typo rate 0.01; markdown breakage none; dangling references 3; TBD markers 2

Service: Back-office API for merchants to view settlements, manage users and download reports. (Meridian Pay, external exposure, data: pii, internal)

Components:
- Portal Gateway (api_gateway)
- portal-backend (service)
- portal-db (PostgreSQL) (database)
- Keycloak (identity_provider)
- Merchant web app (client_app)

Flows:
- Merchant web app -> Portal Gateway: settlement queries and user management
- Portal Gateway -> Keycloak: token validation
- Portal Gateway -> portal-backend: authenticated requests
- portal-backend -> portal-db (PostgreSQL): settlements and merchant users

Implementation (openapi) the document describes:
- GET /v1/settlements: List settlements
- GET /v1/settlements/{settlementId}: Get a settlement
- POST /v1/users: Invite a merchant user
- PATCH /v1/users/{userId}/role: Change a merchant user role
- POST /v1/reports: Request a transaction report
- GET /v1/reports/{reportId}/download: Download a finished report

## Planted items
- F1 [drift, critical] State as plain fact, adapted to this service: All state-changing operations require an authenticated caller. Wrap the sentence(s) in the F1 marker.
- F2 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Bot and abuse protection is postponed until there is a measured problem.
- F3 [drift, critical] State as plain fact, adapted to this service: Card numbers are never returned by the API. Wrap the sentence(s) in the F3 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:CRYPTO-06|...⟧ Encryption keys must be held in KMS, never stored with the data they protect, and rotated at least annually.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:DATA-04|...⟧ Non-production environments must not contain real personal or card data.
- ⟦S:API-01|...⟧ All external inputs must be validated against a schema and rejected if invalid.
- ⟦S:API-03|...⟧ Outbound and inbound webhook payloads must be signed and signatures verified.
- ⟦S:API-04|...⟧ Error responses must not reveal stack traces, SQL or internal hostnames.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- ⟦S:OPS-02|...⟧ Containers must run as a non-root user with a read-only root filesystem where possible.
- ⟦S:CRYPTO-07|...⟧ Services must validate TLS certificates and must not disable verification.
- ⟦S:NET-04|...⟧ Services calling third parties must have egress restricted to an approved allowlist.

## Functional content (no security claims)
Aim for at least 1800 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.
Functional detail to describe for each endpoint:
- GET /v1/settlements: request fields none; response fields id, period, gross, fees, net
- GET /v1/settlements/{settlementId}: request fields none; response fields id, period, gross, fees, net
- POST /v1/users: request fields email, role; response fields id, email, role
- PATCH /v1/users/{userId}/role: request fields role; response fields id, email, role
- POST /v1/reports: request fields report_type, from_date, to_date; response fields id, status, expires_at
- GET /v1/reports/{reportId}/download: request fields none; response fields id, status, expires_at

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c015_merchant_portal_api/design_marked.md
