# Writer brief: c124_payment_gateway

Author profile `buzzword_pm`: Business framing, security stated as adjectives ("enterprise-grade", "secure by design") with no mechanisms.
- structure=clean_headings, english=native_fluent, hedging=none, terminology=wrong_terms, staleness=none
- typical gaps: every concrete control, algorithms, token lifetimes, network boundaries
- length 900-1600 words; typo rate 0.0; markdown breakage none; dangling references 0; TBD markers 0

Service: Accepts card payments from merchants, routes to acquirers, publishes payment events. (Meridian Pay, external exposure, data: card_data, pii)

Components:
- Payments Edge Gateway (api_gateway)
- payments-core (service)
- payments-db (PostgreSQL) (database)
- Acquirer connector (third_party)
- payment-events (Kafka) (message_queue)

Flows:
- Merchant backend -> Payments Edge Gateway: payment request with card token
- Payments Edge Gateway -> payments-core: validated payment request
- payments-core -> payments-db (PostgreSQL): payment records
- payments-core -> Acquirer connector: authorization request
- payments-core -> payment-events (Kafka): payment status events

Implementation (openapi) the document describes:
- POST /v1/payments: Create a payment
- GET /v1/payments/{paymentId}: Retrieve a payment
- POST /v1/payments/{paymentId}/capture: Capture an authorized payment
- POST /v1/payments/{paymentId}/refunds: Refund a payment
- GET /v1/payments: List payments

## Planted items
- F1 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The HTTP client accepts any certificate when calling the partner to avoid trust store updates.
- F2 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The service can reach any address on the internet; no egress rules exist.
- F3 [ambiguity, medium] Mention Payments Edge Gateway naturally, but do NOT state: Behavior after repeated failed logins. Wrap the sentence(s) that mention Payments Edge Gateway (the place where that information should have been) in the F3 marker.
- F4 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Containers write to the host file system as root to keep logs.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTH-01|...⟧ Every externally reachable API endpoint must authenticate callers with OAuth2/OIDC bearer tokens or mutual TLS.
- ⟦S:AUTH-03|...⟧ Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- ⟦S:AUTHZ-01|...⟧ Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:CRYPTO-02|...⟧ Primary account numbers must never be stored in clear text and must be tokenized by the card token vault.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:CRYPTO-06|...⟧ Encryption keys must be held in KMS, never stored with the data they protect, and rotated at least annually.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:DATA-05|...⟧ Reports and exports containing personal data must require authorization, be encrypted in storage and expire.
- ⟦S:CRYPTO-04|...⟧ Traffic between services and to data stores must be encrypted in transit.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:NET-05|...⟧ External APIs must sit behind a WAF with rate limiting.
- ⟦S:LOG-04|...⟧ Access to centralized logs must be limited to authorized staff.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:DATA-04|...⟧ Non-production environments must not contain real personal or card data.
- ⟦S:API-01|...⟧ All external inputs must be validated against a schema and rejected if invalid.
- ⟦S:API-03|...⟧ Outbound and inbound webhook payloads must be signed and signatures verified.
- ⟦S:API-04|...⟧ Error responses must not reveal stack traces, SQL or internal hostnames.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- ⟦S:OPS-03|...⟧ Backups must be encrypted and restoration must be tested at least twice a year.
- ⟦S:DATA-01|...⟧ Services must collect and store only the personal data needed for their purpose.
- ⟦S:CRYPTO-03|...⟧ All external traffic must use TLS 1.2 or higher.

## Functional content (no security claims)
Aim for at least 900 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.
Functional detail to describe for each endpoint:
- POST /v1/payments: request fields amount, currency, card_token, merchant_id, reference; response fields id, status, amount, currency, last4, merchant_id
- GET /v1/payments/{paymentId}: request fields none; response fields id, status, amount, currency, last4, merchant_id
- POST /v1/payments/{paymentId}/capture: request fields amount; response fields id, status, amount, currency, last4, merchant_id
- POST /v1/payments/{paymentId}/refunds: request fields amount, reason; response fields id, status, amount
- GET /v1/payments: request fields none; response fields id, status, amount, currency, last4, merchant_id

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c124_payment_gateway/design_marked.md
