# Writer brief: c082_wallet_service

Author profile `meeting_notes`: Written as decisions and open questions after a design meeting; some decisions are reversed later in the same doc.
- structure=meeting_notes, english=native_sloppy, hedging=high, terminology=aliases_drift, staleness=none
- typical gaps: final outcome of open questions
- length 700-1400 words; typo rate 0.03; markdown breakage none; dangling references 0; TBD markers 2

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
- F1 [ambiguity, high] Mention Mobile API Gateway naturally, but do NOT state: Which mechanism authenticates callers of the public endpoints. Wrap the sentence(s) that mention Mobile API Gateway (the place where that information should have been) in the F1 marker.
- F2 [ambiguity, high] Mention Mobile API Gateway naturally, but do NOT state: Where administrative endpoints are exposed and to whom. Wrap the sentence(s) that mention Mobile API Gateway (the place where that information should have been) in the F2 marker.
- F3 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The allow-list of origins is empty, which the gateway treats as allow everything.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTH-05|...⟧ Passwords must be stored only as salted hashes using argon2id or bcrypt and never in reversible form.
- ⟦S:AUTHZ-03|...⟧ Each service must use its own database account with the minimum grants and no shared administrative credentials.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:NET-05|...⟧ External APIs must sit behind a WAF with rate limiting.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:DATA-02|...⟧ Personal data must have a defined retention period and be deleted when it expires or on verified request.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:API-01|...⟧ All external inputs must be validated against a schema and rejected if invalid.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- ⟦S:OPS-02|...⟧ Containers must run as a non-root user with a read-only root filesystem where possible.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:CRYPTO-03|...⟧ All external traffic must use TLS 1.2 or higher.

## Functional content (no security claims)
Aim for at least 700 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c082_wallet_service/design_marked.md
