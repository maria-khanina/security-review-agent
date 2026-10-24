# Writer brief: c010_wallet_service

Author profile `diagram_narrator`: Mostly an ASCII or mermaid diagram plus short captions; flows exist only as arrows between boxes.
- structure=diagram_narration, english=jargon_dense, hedging=none, terminology=consistent, staleness=none
- typical gaps: trust boundaries, credentials on arrows, protocols on arrows
- length 500-1100 words; typo rate 0.01; markdown breakage light; dangling references 0; TBD markers 0

Service: Consumer wallet balances, top-ups and peer-to-peer transfers. (Meridian Pay, external exposure, data: pii, credentials)

Components:
- Mobile API Gateway (api_gateway)
- wallet-core (service)
- wallet-db (PostgreSQL) (database)
- Keycloak (identity_provider)

Flows:
- Mobile app -> Mobile API Gateway: wallet and transfer requests
- Mobile API Gateway -> Keycloak: token validation
- Mobile API Gateway -> wallet-core: authenticated requests
- wallet-core -> wallet-db (PostgreSQL): balances and transactions

Implementation (openapi) the document describes:
- GET /v1/wallets/{walletId}: Retrieve wallet and balance
- POST /v1/wallets/{walletId}/topups: Top up a wallet from a funding source
- POST /v1/transfers: Transfer money between wallets
- GET /v1/wallets/{walletId}/transactions: List wallet transactions
- PATCH /v1/wallets/{walletId}/profile: Update wallet owner profile

## Planted items
- F1 [violation, critical] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Passwords are hashed with plain SHA-256 without a per-user salt.
- F2 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Backups are copied to a separate account without encryption.
- F3 [ambiguity, low] Mention wallet-db (PostgreSQL) naturally, but do NOT state: How long personal data is kept and how it is deleted. Wrap the sentence(s) that mention wallet-db (PostgreSQL) (the place where that information should have been) in the F3 marker.
- F4 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The service image keeps the default root user because changing it broke file access.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:CRYPTO-06|...⟧ Encryption keys must be held in KMS, never stored with the data they protect, and rotated at least annually.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:DATA-04|...⟧ Non-production environments must not contain real personal or card data.
- ⟦S:CRYPTO-07|...⟧ Services must validate TLS certificates and must not disable verification.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:API-02|...⟧ External APIs must enforce per-client rate limits.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:NET-05|...⟧ External APIs must sit behind a WAF with rate limiting.
- ⟦S:AUTH-03|...⟧ Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- ⟦S:NET-04|...⟧ Services calling third parties must have egress restricted to an approved allowlist.
- ⟦S:CRYPTO-04|...⟧ Traffic between services and to data stores must be encrypted in transit.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:API-01|...⟧ All external inputs must be validated against a schema and rejected if invalid.
- ⟦S:API-03|...⟧ Outbound and inbound webhook payloads must be signed and signatures verified.
- ⟦S:API-04|...⟧ Error responses must not reveal stack traces, SQL or internal hostnames.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:AUTHZ-01|...⟧ Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.

## Functional content (no security claims)
Aim for at least 500 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.
Functional detail to describe for each endpoint:
- GET /v1/wallets/{walletId}: request fields none; response fields id, owner_name, balance, currency
- POST /v1/wallets/{walletId}/topups: request fields amount, funding_source_id; response fields id, type, amount, created_at
- POST /v1/transfers: request fields from_wallet_id, to_wallet_id, amount, note; response fields id, type, amount, created_at
- GET /v1/wallets/{walletId}/transactions: request fields none; response fields id, type, amount, created_at
- PATCH /v1/wallets/{walletId}/profile: request fields owner_name, phone_number, address; response fields id, owner_name, balance, currency

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c010_wallet_service/design_marked.md
