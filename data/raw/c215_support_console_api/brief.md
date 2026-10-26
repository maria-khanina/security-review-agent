# Writer brief: c215_support_console_api

Author profile `slack_paste`: Chat excerpts pasted into the doc with names, informal tone and half-sentences; decisions are implicit.
- structure=chat_paste, english=native_sloppy, hedging=high, terminology=aliases_drift, staleness=none
- typical gaps: anything said in a thread that was not pasted
- length 600-1300 words; typo rate 0.03; markdown breakage light; dangling references 0; TBD markers 2

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
- F1 [violation, critical] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Queries add the tenant filter in some handlers and rely on the caller in others.
- F2 [ambiguity, low] Mention console-backend naturally, but do NOT state: What procedure the service follows when a security incident happens. Wrap the sentence(s) that mention console-backend (the place where that information should have been) in the F2 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:TEN-02|...⟧ Tenant data in shared storage should be separated by row-level security or by tenant-specific encryption keys.
- ⟦S:PAY-02|...⟧ Refunds and reversals above 1,000 EUR must be approved by a second person, and the person who requested the operation must not be able to approve it.
- ⟦S:UPL-01|...⟧ Uploaded files must not exceed 10 MB, and their type must be checked against an allowed list on the content of the file, not on its name.
- ⟦S:UPL-02|...⟧ Uploaded files must be scanned for malware before any other user or service can open them.
- ⟦S:TPC-02|...⟧ Third-party scripts must not be loaded into web pages that handle card data or credentials.
- ⟦S:TPC-01|...⟧ Every third-party SDK or library must be approved before its first use, and the list of approved components must be reviewed every six months.
- ⟦S:IR-01|...⟧ Alerts about repeated failed logins, privilege changes and access to card data must reach the on-call engineer within 15 minutes.
- ⟦S:DR-01|...⟧ Databases must have point-in-time recovery enabled with at least seven days of retention.
- ⟦S:DR-02|...⟧ The recovery time objective of a critical service must not exceed 4 hours, and it must be proven by a failover exercise at least once a year.

## Functional content (no security claims)
Aim for at least 600 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c215_support_console_api/design_marked.md
