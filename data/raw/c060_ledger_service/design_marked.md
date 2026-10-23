# Ledger Service: Product Brief and Design

Owner: Finance Platform Product
Status: Approved for build
Background: see the earlier "Ledger discovery" write-up (link may be stale)

## 1. Why now

Every money product we ship relies on the same question: what is the true balance of this account right now? Today the answer is spread across wallet tables, payment tables and spreadsheets. The Ledger Service gives Meridian Pay one authoritative, enterprise-grade, secure-by-design record of every movement of money.

The first release delivers three outcomes: one balance per account that every product agrees on, one place for finance to reconcile, and a full history that auditors can follow without asking engineers.

## 2. Value

- Customers see the same balance in the app, on statements and when they call support.
- Finance reconciles faster and with less manual work.
- Product teams stop building their own bookkeeping.
- Compliance receives an ordered, tamper-evident history of money movements.

## 3. How it works

Wallet and payment services send journal entries to ledger-core. ledger-core checks that each entry balances, stores it in ledger-db (PostgreSQL) and announces it on ledger-events (Kafka). Other teams subscribe to those announcements, for example notifications and analytics.

⟦F1|ledger-core accepts entries only from the wallet and payment services of the platform.⟧

The API has five operations. POST /v1/entries posts an entry (debit_account, credit_account, amount, currency, reference) and returns it with its id and posting time. GET /v1/entries/{entryId} returns one entry. GET /v1/accounts/{accountId}/balance returns the account's balance and currency. POST /v1/entries/{entryId}/reversal posts a cancelling entry for a given reason. GET /v1/entries lists entries.

⟦F2|Requests are validated against strict schemas.⟧ Entries in two different currencies are rejected, and an entry must balance to be accepted.

## 4. Principles

Double entry (every entry has a debit and a credit side that balance), immutability (entries are never edited or deleted, mistakes are corrected with reversals), derivation (balances are calculated from entries) and idempotency (the same reference posted twice returns the original entry). These four principles are the contract of the ledger, and every feature is judged against them.

## 5. Data

An entry has an id, two accounts, an amount in minor units, a currency, a reference and a posting time. A balance has an account, an amount and a currency. A reversal is an entry that points to the entry it cancels. The data model is deliberately small.

## 6. Quality

Posting is transactional: an entry either appears in full or not at all, and its announcement is published only after it is stored. If the event stream is unavailable, entries are still accepted and announcements catch up later. A nightly reconciliation compares the sum of all entries with the sum of all balances and alerts on any difference.

## 7. Security and compliance posture

Security is a first-class feature of the ledger. The commitments below are the ones we make to finance and auditors.

- ⟦S:AUTHZ-02|Internal users receive only the roles required for their job, and roles are defined per service.⟧
- ⟦S:AUTHZ-05|Access rights to production systems are reviewed at least quarterly.⟧
- ⟦S:SECRET-01|Secrets are never stored in source code, configuration files, specifications or infrastructure definitions.⟧
- ⟦S:NET-01|ledger-db and the Kafka brokers sit in private subnets and are not publicly reachable.⟧
- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧
- ⟦S:API-05|All database queries are parameterized, and concatenating user input into queries is prohibited.⟧

Reconciliation reports are shared with finance through download links. ⟦F3|The download links carry a signed token whose signature is an HMAC based on MD5, because the library defaults to it.⟧

## 8. Rollout

Rollout follows the money, in three waves. Wave one mirrors entries from the old wallet tables in shadow mode so finance can compare. Wave two makes the ledger authoritative for wallet balances. Wave three moves payments. After each wave finance signs off on a full day of reconciliation before the next wave starts (the sign-off template is TBD).

## 9. Open questions

- Should the balance endpoint cache for a second under heavy read load? Finance prefers no cache.
- Page size of the entry list: support asked for fifty (TBD).
