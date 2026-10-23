# Ledger Service: Product and Design Overview

Owner: Finance Platform Product
Status: Approved for build

## 1. Why a ledger?

Money is the one thing our customers never forgive us for getting wrong. Every wallet top-up, every payment and every refund must be recorded in a way that finance can trust, auditors can follow and engineers can reason about. The Ledger Service is the single source of financial truth for Meridian Pay: an enterprise-grade, secure-by-design record of who owes what to whom, written once and never edited.

The first release delivers three outcomes: wallet and payment teams stop keeping their own balance tables, finance can reconcile any account from one place, and every movement of money is explainable in one sentence.

## 2. Customer and business value

- Customers see balances that are always consistent across the app, the statements and support conversations.
- Finance closes the books faster because there is only one record to reconcile.
- Product teams ship money features without reinventing bookkeeping.
- Risk and compliance get a complete, ordered history of every movement.

## 3. Principles

The ledger is built on a small number of principles that every feature must respect. First, double entry: every entry has a debit side and a credit side and they must balance. Second, immutability: an entry is never changed or deleted; mistakes are fixed by posting a reversal. Third, derivation: balances are calculated from entries and never edited directly. Fourth, idempotency: posting the same reference twice returns the original entry, so retries are safe.

## 4. How it works

Wallet and payment services send journal entries to ledger-core. ledger-core checks that the entry balances, writes it to ledger-db (PostgreSQL) and announces it on ledger-events (Kafka) so that other teams, for example notifications and analytics, can react in real time.

⟦F1|ledger-core starts with the standard platform bootstrap and is ready to accept entries a few seconds later.⟧ ⟦F2|ledger-db (PostgreSQL) is the system of record and holds every entry and every derived balance.⟧ ⟦F3|ledger-core protects the integrity and confidentiality of the entries it handles in line with our enterprise standards.⟧

## 5. Capabilities

**Post an entry.** POST /v1/entries accepts a debit_account, a credit_account, an amount, a currency and a reference. It returns the posted entry with its id, both accounts, the amount and the posting time. Entries in two different currencies are rejected; conversion is the caller's job.

**Look up an entry.** GET /v1/entries/{entryId} returns one entry in the same shape, which support uses when a customer asks about a specific movement.

**See a balance.** GET /v1/accounts/{accountId}/balance returns the account, its balance and the currency. The balance is the sum of all entries for the account.

**Reverse an entry.** POST /v1/entries/{entryId}/reversal posts a new entry that exactly cancels the original. The only input is a reason, which is stored with the reversal for the audit trail. An entry can be reversed once.

**Browse entries.** GET /v1/entries lists entries, newest first, so that finance and support can follow the flow of money.

## 6. Data model

An entry has an id, a debit account, a credit account, an amount in minor units, a currency, a reference and a posting time. A balance has an account, an amount and a currency. There are no other tables of substance. The simplicity is deliberate: fewer moving parts means fewer ways to be wrong.

## 7. Quality and reliability

The ledger is designed for correctness before speed. Posting is transactional, so an entry either appears in full or not at all, and the event is announced only after the entry is stored. If the event stream is unavailable, entries are still accepted and the announcements catch up when the stream returns. Reconciliation jobs compare the sum of all entries to the sum of all balances every night and alert on any difference.

## 8. Security and compliance posture

Security is a first-class feature of the Ledger Service. The commitments below are the ones we make to finance, to auditors and to the compliance team.

- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧
- ⟦S:API-05|All database queries are parameterized, and concatenating user input into queries is prohibited.⟧
- ⟦S:OPS-01|CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧

Access to the database is handled with the same care. ⟦F4|The application uses the database owner account because creating separate grants was too slow for the first release.⟧ We plan to revisit this once the schema settles.

## 9. Rollout

Rollout follows the money. Wave one mirrors entries from the old wallet tables into the ledger in shadow mode so that finance can compare. Wave two makes the ledger authoritative for wallet balances. Wave three moves payments. After each wave, finance signs off on a full day of reconciliation before the next begins. A switch allows any wave to fall back to the old tables during the shadow and authoritative phases.

## 10. Open questions

- Should the balance endpoint cache for a second under heavy read load? Finance prefers no cache.
- What is the right page size for the entry list? Support asked for fifty.
