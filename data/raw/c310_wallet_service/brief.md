# Writer brief: c050_wallet_service

Author profile `merged_two_authors`: Two people wrote different halves; heading levels, terminology and level of detail change midway and sections disagree.
- structure=merged_voices, english=native_sloppy, hedging=low, terminology=aliases_drift, staleness=some_outdated
- typical gaps: consistency between the halves
- length 1500-2600 words; typo rate 0.01; markdown breakage heavy; dangling references 0; TBD markers 0

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
- F1 [violation, critical] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): A fast hash with a single global salt is used for passwords.
- F2 [ambiguity, high] Mention wallet-core naturally, but do NOT state: How queries are constructed from request parameters. Wrap the sentence(s) that mention wallet-core (the place where that information should have been) in the F2 marker.
- F3 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Allowed origins are not configured; the gateway reflects the request origin.
- F4 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Privilege changes are applied by administrators directly in the database and leave no trace.
- F5 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Customer data is shared with a new provider while the contract is still being negotiated.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:NET-05|...⟧ External APIs must sit behind a WAF with rate limiting.
- ⟦S:CRYPTO-04|...⟧ Traffic between services and to data stores must be encrypted in transit.
- ⟦S:AUTHZ-03|...⟧ Each service must use its own database account with the minimum grants and no shared administrative credentials.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:OPS-02|...⟧ Containers must run as a non-root user with a read-only root filesystem where possible.
- ⟦S:DATA-02|...⟧ Personal data must have a defined retention period and be deleted when it expires or on verified request.
- ⟦S:API-01|...⟧ All external inputs must be validated against a schema and rejected if invalid.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.

## Functional content (no security claims)
Aim for at least 1500 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c050_wallet_service/design_marked.md
