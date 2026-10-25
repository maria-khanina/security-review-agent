# Writer brief: c511_merchant_portal_api

Author profile `table_lover`: Everything in tables (components, endpoints, data stores); prose is minimal and some tables are malformed.
- structure=tables_only, english=jargon_dense, hedging=none, terminology=consistent, staleness=none
- typical gaps: reasons and conditions that do not fit a table cell
- length 600-1300 words; typo rate 0.0; markdown breakage heavy; dangling references 1; TBD markers 2

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
- F1 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Artifacts are copied from the build server to production without signatures.
- F2 [ambiguity, medium] Mention portal-db (PostgreSQL) naturally, but do NOT state: In which regions the backups and replicas of personal data are kept. Wrap the sentence(s) that mention portal-db (PostgreSQL) (the place where that information should have been) in the F2 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:PRV-01|...⟧ Requests of customers to see or delete their personal data must be answered within 30 days and recorded in the request register.
- ⟦S:PRV-02|...⟧ Consent to marketing messages must be recorded with its time and the version of the wording, and a withdrawal must stop the messages within 24 hours.
- ⟦S:CHG-02|...⟧ Every change to production must have a rollback plan that has been tested in a pre-production environment.
- ⟦S:PIP-01|...⟧ Credentials of the delivery pipeline must be issued for each run and be valid for at most 1 hour.
- ⟦S:OBS-01|...⟧ Traces and metrics must not contain personal data or card data.
- ⟦S:CAP-01|...⟧ Public endpoints must shed load with HTTP 503 instead of queueing requests when their capacity is exhausted.

## Functional content (no security claims)
Aim for at least 600 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c511_merchant_portal_api/design_marked.md
