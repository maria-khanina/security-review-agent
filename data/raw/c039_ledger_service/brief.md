# Writer brief: c039_ledger_service

Author profile `buzzword_pm`: Business framing, security stated as adjectives ("enterprise-grade", "secure by design") with no mechanisms.
- structure=clean_headings, english=native_fluent, hedging=none, terminology=wrong_terms, staleness=none
- typical gaps: every concrete control, algorithms, token lifetimes, network boundaries
- length 900-1600 words; typo rate 0.01; markdown breakage none; dangling references 0; TBD markers 0

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
- F1 [ambiguity, low] Mention ledger-core naturally, but do NOT state: How the service obtains its secrets at runtime. Wrap the sentence(s) that mention ledger-core (the place where that information should have been) in the F1 marker.
- F2 [ambiguity, low] Mention ledger-db (PostgreSQL) naturally, but do NOT state: Network placement of the database or broker. Wrap the sentence(s) that mention ledger-db (PostgreSQL) (the place where that information should have been) in the F2 marker.
- F3 [ambiguity, low] Mention ledger-core naturally, but do NOT state: Which algorithms protect integrity and confidentiality. Wrap the sentence(s) that mention ledger-core (the place where that information should have been) in the F3 marker.
- F4 [violation, medium] State, as the author naturally would and believing it acceptable, a design decision of this kind (use your own words and this service's context; do not copy the wording): The application uses the database owner account because creating grants was too slow.

## Required compliance statements
State each of these concretely (terse is fine for terse profiles) and wrap the statement in the marker shown.
- ⟦S:LOG-01|...⟧ Authentication failures, privilege changes and access to sensitive data must be logged.
- ⟦S:API-05|...⟧ Database queries must be parameterized; string concatenation of user input into queries is prohibited.
- ⟦S:OPS-01|...⟧ CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.

## Functional content (no security claims)
Aim for at least 900 words in total. Reach the length with functional detail written in the author's voice, never with extra security statements.
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
- Save to data/raw/c039_ledger_service/design_marked.md
