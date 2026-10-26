# Writer brief: c116_refund_service

Author profile `slack_paste`: Chat excerpts pasted into the doc with names, informal tone and half-sentences; decisions are implicit.
- structure=chat_paste, english=native_sloppy, hedging=high, terminology=aliases_drift, staleness=none
- typical gaps: anything said in a thread that was not pasted
- length 600-1300 words; typo rate 0.03; markdown breakage heavy; dangling references 0; TBD markers 5

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
- F1 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The API accepts any JSON object and the service picks the fields it needs.
- F2 [ambiguity, high] Mention refund-db (PostgreSQL) naturally, but do NOT state: Which database identity each service uses and its grants. Wrap the sentence(s) that mention refund-db (PostgreSQL) (the place where that information should have been) in the F2 marker.
- F3 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Rate limiting is left for a later release; there are no per-client limits at launch.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:AUTH-01|...⟧ Every externally reachable API endpoint must authenticate callers with OAuth2/OIDC bearer tokens or mutual TLS.
- ⟦S:AUTHZ-01|...⟧ Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.
- ⟦S:AUTHZ-04|...⟧ Administrative and debug endpoints must not be reachable from the public internet.
- ⟦S:CRYPTO-04|...⟧ Traffic between services and to data stores must be encrypted in transit.
- ⟦S:CRYPTO-01|...⟧ Personally identifiable information must be encrypted at rest with AES-256 or stronger.
- ⟦S:CRYPTO-02|...⟧ Primary account numbers must never be stored in clear text and must be tokenized by the card token vault.
- ⟦S:CRYPTO-05|...⟧ Only approved cryptographic algorithms may be used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- ⟦S:SECRET-01|...⟧ Secrets must not appear in source code, configuration files, specifications or infrastructure definitions.
- ⟦S:SECRET-02|...⟧ Runtime secrets must be fetched from the approved secret store at startup.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:LOG-02|...⟧ Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- ⟦S:DATA-02|...⟧ Personal data must have a defined retention period and be deleted when it expires or on verified request.
- ⟦S:DATA-03|...⟧ Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- ⟦S:AUTH-02|...⟧ Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- ⟦S:OPS-02|...⟧ Containers must run as a non-root user with a read-only root filesystem where possible.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:API-06|...⟧ Browser-facing APIs must allow only approved origins in CORS.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.
- ⟦S:AUTH-03|...⟧ Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- ⟦S:OPS-03|...⟧ Backups must be encrypted and restoration must be tested at least twice a year.
- ⟦S:NET-01|...⟧ Databases and message brokers must not be publicly reachable and must live in private subnets.
- ⟦S:CRYPTO-03|...⟧ All external traffic must use TLS 1.2 or higher.

## Functional content (no security claims)
Aim for at least 600 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c116_refund_service/design_marked.md
