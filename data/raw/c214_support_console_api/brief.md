# Writer brief: c214_support_console_api

Author profile `merged_two_authors`: Two people wrote different halves; heading levels, terminology and level of detail change midway and sections disagree.
- structure=merged_voices, english=native_sloppy, hedging=low, terminology=aliases_drift, staleness=some_outdated
- typical gaps: consistency between the halves
- length 1500-2600 words; typo rate 0.03; markdown breakage light; dangling references 0; TBD markers 2

Service: Back-office API for support agents to look up customers, reset second factors and issue goodwill credits. (Meridian Pay, admin exposure, data: pii, credentials)

Components:
- console-backend (service)
- console-db (PostgreSQL) (database)
- Keycloak (identity_provider)
- Support web console (client_app)

Flows:
- Support web console -> console-backend: customer lookups and account actions
- console-backend -> Keycloak: agent token validation
- console-backend -> console-db (PostgreSQL): customer profiles and agent action records

Implementation (openapi) the document describes:
- GET /v1/customers: Search customers
- GET /v1/customers/{customerId}: Retrieve a customer profile
- POST /v1/customers/{customerId}/second-factor-reset: Reset the second factor of a customer
- POST /v1/customers/{customerId}/credits: Issue a goodwill credit
- GET /v1/agent-actions: List actions taken by support agents
- POST /v1/customers/{customerId}/data-export: Export the data held about a customer

## Planted items
- F1 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Files are checked by the antivirus on the laptop of the person who downloads them.
- F2 [violation, critical] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Approval is recorded in a spreadsheet and is not enforced by the service.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:TEN-01|...⟧ Every query on merchant data must be filtered by the tenant identifier taken from the authenticated token and never from a request parameter.
- ⟦S:TPC-02|...⟧ Third-party scripts must not be loaded into web pages that handle card data or credentials.
- ⟦S:IR-01|...⟧ Alerts about repeated failed logins, privilege changes and access to card data must reach the on-call engineer within 15 minutes.
- ⟦S:DR-01|...⟧ Databases must have point-in-time recovery enabled with at least seven days of retention.
- ⟦S:TPC-01|...⟧ Every third-party SDK or library must be approved before its first use, and the list of approved components must be reviewed every six months.
- ⟦S:IR-02|...⟧ Every service must have a written incident runbook, a named on-call owner and a rehearsal at least twice a year.

## Functional content (no security claims)
Aim for at least 1500 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.
Functional detail to describe for each endpoint:
- GET /v1/customers: request fields none; response fields id, full_name, email, phone_number, status
- GET /v1/customers/{customerId}: request fields none; response fields id, full_name, email, phone_number, status
- POST /v1/customers/{customerId}/second-factor-reset: request fields reason, ticket_id; response fields id, status
- POST /v1/customers/{customerId}/credits: request fields amount, currency, reason, ticket_id; response fields id, amount, currency, status
- GET /v1/agent-actions: request fields none; response fields id, agent_id, action, created_at
- POST /v1/customers/{customerId}/data-export: request fields format, reason; response fields id, status, expires_at

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c214_support_console_api/design_marked.md
