# Writer brief: c094_wallet_service

Author profile `slack_paste`: Chat excerpts pasted into the doc with names, informal tone and half-sentences; decisions are implicit.
- structure=chat_paste, english=native_sloppy, hedging=high, terminology=aliases_drift, staleness=none
- typical gaps: anything said in a thread that was not pasted
- length 600-1300 words; typo rate 0.01; markdown breakage heavy; dangling references 0; TBD markers 2

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
- F1 [ambiguity, medium] Mention wallet-core naturally, but do NOT state: What data is shared with the vendor and under what agreement. Wrap the sentence(s) that mention wallet-core (the place where that information should have been) in the F1 marker.
- F2 [violation, critical] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Dynamic ordering uses the sort parameter directly in the SQL statement.
- F3 [ambiguity, medium] Mention wallet-core naturally, but do NOT state: Retention and tamper protection of audit logs. Wrap the sentence(s) that mention wallet-core (the place where that information should have been) in the F3 marker.
- F4 [violation, critical] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Signature verification is skipped for callbacks from the partner sandbox.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTH-01|...⟧ Every externally reachable API endpoint must authenticate callers with OAuth2/OIDC bearer tokens or mutual TLS.
- ⟦S:AUTH-03|...⟧ Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- ⟦S:AUTH-05|...⟧ Passwords must be stored only as salted hashes using argon2id or bcrypt and never in reversible form.
- ⟦S:AUTH-06|...⟧ Login and token endpoints must throttle or lock out repeated failed attempts.
- ⟦S:CRYPTO-04|...⟧ Traffic between services and to data stores must be encrypted in transit.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:AUTHZ-01|...⟧ Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:CRYPTO-06|...⟧ Encryption keys must be held in KMS, never stored with the data they protect, and rotated at least annually.
- ⟦S:CRYPTO-07|...⟧ Services must validate TLS certificates and must not disable verification.
- ⟦S:API-02|...⟧ External APIs must enforce per-client rate limits.
- ⟦S:NET-05|...⟧ External APIs must sit behind a WAF with rate limiting.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:NET-04|...⟧ Services calling third parties must have egress restricted to an approved allowlist.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:DATA-04|...⟧ Non-production environments must not contain real personal or card data.
- ⟦S:LOG-04|...⟧ Access to centralized logs must be limited to authorized staff.
- ⟦S:AUTHZ-03|...⟧ Each service must use its own database account with the minimum grants and no shared administrative credentials.
- ⟦S:API-01|...⟧ All external inputs must be validated against a schema and rejected if invalid.
- ⟦S:API-04|...⟧ Error responses must not reveal stack traces, SQL or internal hostnames.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- ⟦S:OPS-02|...⟧ Containers must run as a non-root user with a read-only root filesystem where possible.
- ⟦S:OPS-03|...⟧ Backups must be encrypted and restoration must be tested at least twice a year.
- ⟦S:SECRET-03|...⟧ Service credentials must be rotated at least every 90 days and immediately after suspected exposure.
- ⟦S:DATA-01|...⟧ Services must collect and store only the personal data needed for their purpose.
- ⟦S:CRYPTO-03|...⟧ All external traffic must use TLS 1.2 or higher.

## Functional content (no security claims)
Aim for at least 600 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c094_wallet_service/design_marked.md
