# Writer brief: c503_wallet_service

Author profile `ticket_writer`: Jira style with user stories, numbered requirements and acceptance criteria; non-functional requirements are afterthoughts.
- structure=ticket_style, english=native_fluent, hedging=low, terminology=consistent, staleness=none
- typical gaps: security as acceptance criteria, data classification
- length 900-1700 words; typo rate 0.0; markdown breakage none; dangling references 1; TBD markers 0

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
- F1 [violation, critical] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Database migrations cannot be rolled back, and nothing is planned for that.
- F2 [violation, critical] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Error traces include the card number that failed validation.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:PRV-01|...⟧ Requests of customers to see or delete their personal data must be answered within 30 days and recorded in the request register.
- ⟦S:RES-02|...⟧ Backups and replicas of personal data of customers in the EU should stay in regions of the EU as well.
- ⟦S:PIP-01|...⟧ Credentials of the delivery pipeline must be issued for each run and be valid for at most 1 hour.
- ⟦S:PIP-02|...⟧ Build artifacts must be signed, and the signature must be verified before deployment.
- ⟦S:CAP-01|...⟧ Public endpoints must shed load with HTTP 503 instead of queueing requests when their capacity is exhausted.
- ⟦S:CAP-02|...⟧ Every feature that moves money must have a kill switch, and the kill switch must be tested every quarter.
- ⟦S:OBS-02|...⟧ Every service must publish its health check and error rates to the shared dashboard every minute.
- ⟦S:CHG-01|...⟧ Every change to production must be reviewed by a second engineer before it is deployed.
- ⟦S:PRV-03|...⟧ Personal data must be used only for purposes listed in the privacy notice shown to customers at sign-up.

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
- Save to data/raw/c503_wallet_service/design_marked.md
