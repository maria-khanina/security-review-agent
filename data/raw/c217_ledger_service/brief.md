# Writer brief: c217_ledger_service

Author profile `migration_delta_writer`: Describes only what changes relative to the existing system and assumes the old behavior carries over.
- structure=delta_only, english=native_fluent, hedging=low, terminology=consistent, staleness=some_outdated
- typical gaps: security properties inherited from the old system
- length 700-1500 words; typo rate 0.0; markdown breakage light; dangling references 1; TBD markers 0

Service: Double-entry ledger consumed by wallet and payment services. (Meridian Pay, internal exposure, data: internal)

Components:
- ledger-core (service)
- ledger-db (PostgreSQL) (database)
- ledger-events (Kafka) (message_queue)

Flows:
- Wallet and payment services -> ledger-core: journal entries
- ledger-core -> ledger-db (PostgreSQL): entries and balances
- ledger-core -> ledger-events (Kafka): posted entry events

Implementation (openapi) the document describes:
- POST /v1/entries: Post a balanced journal entry
- GET /v1/entries/{entryId}: Retrieve an entry
- GET /v1/accounts/{accountId}/balance: Get account balance
- POST /v1/entries/{entryId}/reversal: Reverse an entry
- GET /v1/entries: List entries

## Planted items
- F1 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): Security alerts are collected on a dashboard that nobody is paged from.
- F2 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The recovery plan assumes a restore from a backup that takes about a day.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:DR-01|...⟧ Databases must have point-in-time recovery enabled with at least seven days of retention.
- ⟦S:IR-02|...⟧ Every service must have a written incident runbook, a named on-call owner and a rehearsal at least twice a year.

## Functional content (no security claims)
Aim for at least 700 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
Suggested sections: Background and goals, Non-goals, Behavior of each endpoint or resource, Data model, Failure modes and retries, Rollout plan, Open questions.
Do not mention authentication, authorization, encryption, secrets, network exposure, logging, retention, third-party data sharing, input validation, rate limits, dependency scanning, containers or backups except through the planted items and required statements above.
Functional detail to describe for each endpoint:
- POST /v1/entries: request fields debit_account, credit_account, amount, currency, reference; response fields id, debit_account, credit_account, amount, posted_at
- GET /v1/entries/{entryId}: request fields none; response fields id, debit_account, credit_account, amount, posted_at
- GET /v1/accounts/{accountId}/balance: request fields none; response fields account_id, balance, currency
- POST /v1/entries/{entryId}/reversal: request fields reason; response fields id, debit_account, credit_account, amount, posted_at
- GET /v1/entries: request fields none; response fields id, debit_account, credit_account, amount, posted_at

## Rules for writing
- Marker syntax: ⟦ID|exact text⟧ with the text unchanged inside; markers must not nest.
- Introduce no other policy violation, ambiguity about a required statement, or contradiction beyond the planted items.
- Typos, sloppy structure, TBDs and stale mentions are welcome but must not hide or alter the planted items or required statements.
- Save to data/raw/c217_ledger_service/design_marked.md
