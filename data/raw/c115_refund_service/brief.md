# Writer brief: c115_refund_service

Author profile `security_champion`: Long dedicated security section with many named controls, but some are aspirational and terms are used loosely.
- structure=clean_headings, english=native_fluent, hedging=none, terminology=wrong_terms, staleness=some_outdated
- typical gaps: implementation status of the controls it lists
- length 1800-2600 words; typo rate 0.01; markdown breakage none; dangling references 0; TBD markers 0

Service: Lets merchants and support agents request, approve and track refunds of card payments. (Meridian Pay, external exposure, data: card_data, pii)

Components:
- Refunds Gateway (api_gateway)
- refund-core (service)
- refund-db (PostgreSQL) (database)
- refund-events (Kafka) (message_queue)

Flows:
- Merchant backend and support agents -> Refunds Gateway: refund requests and approvals
- Refunds Gateway -> refund-core: authenticated refund requests
- refund-core -> refund-db (PostgreSQL): refund records with payment references
- refund-core -> refund-events (Kafka): refund status events

Implementation (openapi) the document describes:
- POST /v1/refunds: Request a refund
- GET /v1/refunds/{refundId}: Retrieve a refund
- GET /v1/refunds: List refunds
- POST /v1/refunds/{refundId}/approval: Approve or reject a refund
- POST /v1/refunds/{refundId}/cancellation: Cancel a pending refund

## Planted items
- F1 [violation, critical] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The full card number is kept with the payment record and returned in the API response for reconciliation.
- F2 [ambiguity, medium] Mention refund-core naturally, but do NOT state: Token lifetime and refresh behavior. Wrap the sentence(s) that mention refund-core (the place where that information should have been) in the F2 marker.
- F3 [drift, critical] State as plain fact, adapted to this service: All traffic is served over HTTPS only. Wrap the sentence(s) in the F3 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTH-01|...⟧ Every externally reachable API endpoint must authenticate callers with OAuth2/OIDC bearer tokens or mutual TLS.
- ⟦S:AUTHZ-01|...⟧ Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:AUTHZ-05|...⟧ Access rights to production systems must be reviewed at least quarterly.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:DATA-01|...⟧ Services must collect and store only the personal data needed for their purpose.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:API-01|...⟧ All external inputs must be validated against a schema and rejected if invalid.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:DATA-05|...⟧ Reports and exports containing personal data must require authorization, be encrypted in storage and expire.

## Functional content (no security claims)
Aim for at least 1800 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.
Functional detail to describe for each endpoint:
- POST /v1/refunds: request fields payment_id, amount, currency, reason, requested_by; response fields id, payment_id, status, amount, currency
- GET /v1/refunds/{refundId}: request fields none; response fields id, payment_id, status, amount, currency
- GET /v1/refunds: request fields none; response fields id, payment_id, status, amount, currency
- POST /v1/refunds/{refundId}/approval: request fields decision, comment; response fields id, payment_id, status, amount, currency
- POST /v1/refunds/{refundId}/cancellation: request fields reason; response fields id, payment_id, status, amount, currency

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c115_refund_service/design_marked.md
