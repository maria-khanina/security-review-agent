# Writer brief: c626_wallet_service

Author profile `stream_of_consciousness`: Long unbroken paragraphs written as thinking aloud, flows described in the order they came to mind.
- structure=wall_of_text, english=native_sloppy, hedging=high, terminology=aliases_drift, staleness=none
- typical gaps: explicit statement of authentication method, which component stores what
- length 900-1800 words; typo rate 0.03; markdown breakage none; dangling references 1; TBD markers 2

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
- F1 [violation, critical] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Callbacks to endpoints of large customers are not signed.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:ARC-01|...⟧ Transaction records must be kept for 7 years and must be deleted within 90 days after that period ends.
- ⟦S:ARC-02|...⟧ Documents uploaded by customers must be deleted within 30 days after the account is closed.
- ⟦S:VUL-02|...⟧ Third-party components must not be more than two major versions behind the latest release, and the service register must show the version of each.
- ⟦S:TST-02|...⟧ Test accounts in production must be removed within 7 days after the test ends.
- ⟦S:INV-02|...⟧ The service register must list for each service the personal data that it processes and every third party that receives data from it.
- ⟦S:FRD-01|...⟧ Transactions above 10,000 EUR must be held for review by the fraud team before they are settled.
- ⟦S:MON-01|...⟧ Alerts of severity high must be acknowledged within 15 minutes.

## Functional content (no security claims)
Aim for at least 900 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c626_wallet_service/design_marked.md
