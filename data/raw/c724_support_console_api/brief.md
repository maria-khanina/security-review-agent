# Writer brief: c724_support_console_api

Author profile `slack_paste`: Chat excerpts pasted into the doc with names, informal tone and half-sentences; decisions are implicit.
- structure=chat_paste, english=native_sloppy, hedging=high, terminology=aliases_drift, staleness=none
- typical gaps: anything said in a thread that was not pasted
- length 600-1300 words; typo rate 0.01; markdown breakage heavy; dangling references 0; TBD markers 5

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
- F1 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Messages with personal data are copied to the log as well.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:REC-01|...⟧ Balances must be reconciled with the ledger every day, and a difference of more than 0.01 EUR must be reported to the finance team within 24 hours.
- ⟦S:REC-02|...⟧ Differences found in a reconciliation must be resolved within 5 working days.
- ⟦S:IDM-01|...⟧ Operations that move money must be idempotent: a repeated request with the same key must not move the money again.
- ⟦S:VER-01|...⟧ A replaced version of an API must be kept for 12 months, and its removal must be announced 90 days in advance.
- ⟦S:SBX-01|...⟧ The sandbox for merchants must contain no real customer data and must run separately from production.
- ⟦S:MSG-01|...⟧ Messages that cannot be processed must be moved to a dead-letter queue and be examined within one working day.
- ⟦S:JOB-01|...⟧ Scheduled jobs must run with their own service account that cannot log in interactively.
- ⟦S:SUP-01|...⟧ Support agents must see card numbers and document numbers only in masked form.

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
- Save to data/raw/c724_support_console_api/design_marked.md
