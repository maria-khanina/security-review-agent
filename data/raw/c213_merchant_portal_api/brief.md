# Writer brief: c213_merchant_portal_api

Author profile `optimistic_roadmapper`: Describes planned features in present tense; future and current state are blurred.
- structure=clean_headings, english=native_fluent, hedging=low, terminology=consistent, staleness=none
- typical gaps: which controls exist today
- length 1200-2200 words; typo rate 0.01; markdown breakage light; dangling references 0; TBD markers 0

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
- F1 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Point-in-time recovery is not enabled, and only a nightly snapshot exists.
- F2 [ambiguity, medium] Mention Portal Gateway naturally, but do NOT state: Which third-party scripts run on the pages that handle card data or credentials. Wrap the sentence(s) that mention Portal Gateway (the place where that information should have been) in the F2 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:TEN-01|...⟧ Every query on merchant data must be filtered by the tenant identifier taken from the authenticated token and never from a request parameter.
- ⟦S:TEN-02|...⟧ Tenant data in shared storage should be separated by row-level security or by tenant-specific encryption keys.
- ⟦S:UPL-02|...⟧ Uploaded files must be scanned for malware before any other user or service can open them.
- ⟦S:DR-02|...⟧ The recovery time objective of a critical service must not exceed 4 hours, and it must be proven by a failover exercise at least once a year.

## Functional content (no security claims)
Aim for at least 1200 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c213_merchant_portal_api/design_marked.md
