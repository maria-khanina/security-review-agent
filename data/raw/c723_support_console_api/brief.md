# Writer brief: c723_support_console_api

Author profile `diagram_narrator`: Mostly an ASCII or mermaid diagram plus short captions; flows exist only as arrows between boxes.
- structure=diagram_narration, english=jargon_dense, hedging=none, terminology=consistent, staleness=none
- typical gaps: trust boundaries, credentials on arrows, protocols on arrows
- length 500-1100 words; typo rate 0.01; markdown breakage light; dangling references 0; TBD markers 0

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
- F1 [violation, high] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The sandbox shares the database server with production in a separate schema.
- F2 [violation, critical] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The code is valid for a day and can be used many times.
- F3 [ambiguity, high] Mention console-backend naturally, but do NOT state: How often balances are reconciled with the ledger and who is told about differences. Wrap the sentence(s) that mention console-backend (the place where that information should have been) in the F3 marker.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:REC-02|...⟧ Differences found in a reconciliation must be resolved within 5 working days.
- ⟦S:LIM-01|...⟧ The daily outgoing transfers of a customer must be limited to the amount in the limit table, and a change of a limit needs the approval of a second employee.
- ⟦S:VER-01|...⟧ A replaced version of an API must be kept for 12 months, and its removal must be announced 90 days in advance.
- ⟦S:VER-02|...⟧ Breaking changes of an API must be released only as a new version of the API.
- ⟦S:MSG-01|...⟧ Messages that cannot be processed must be moved to a dead-letter queue and be examined within one working day.
- ⟦S:JOB-01|...⟧ Scheduled jobs must run with their own service account that cannot log in interactively.
- ⟦S:SUP-01|...⟧ Support agents must see card numbers and document numbers only in masked form.

## Functional content (no security claims)
Aim for at least 500 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c723_support_console_api/design_marked.md
