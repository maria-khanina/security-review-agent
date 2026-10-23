# Ledger service: migration delta (v2)

This document only describes what changes compared with the ledger module inside the old payments monolith. Everything not mentioned here behaves as before. See the wiki page "Ledger v1 behavior" (link TBD) for the baseline.

## Why we are moving

The ledger module shared a release train with payments, so every ledger fix waited for a payments release. Wallet and payment teams also needed to post entries without importing monolith code. Pulling the ledger out gives it its own deployment, its own database and its own event stream.

## What changes

1. **Packaging.** The module becomes a standalone service, ledger-core, deployed as three replicas.
2. **Storage.** Entries and balances move from the monolith schema to a dedicated PostgreSQL database, ledger-db. The old tables stay readable for one release as a rollback path (see "Cutover" below).
3. **Events.** Posted entries are published to ledger-events (Kafka). In v1 consumers polled the table; now they subscribe.
4. **API.** The posting logic is exposed over HTTP instead of in-process calls.

## What does not change

Double-entry rules, rounding, currency handling and the reversal semantics stay exactly as in v1. An entry is still balanced or rejected, balances are still derived from entries and never edited directly, and a reversal still posts a new entry rather than deleting the old one.

## API

ledger-core is called by the wallet and payment services:

- POST /v1/entries posts a balanced entry. Fields: debit_account, credit_account, amount, currency, reference. The reply contains id, debit_account, credit_account, amount and posted_at.
- GET /v1/entries/{entryId} returns one entry in the same shape.
- GET /v1/accounts/{accountId}/balance returns account_id, balance and currency.
- POST /v1/entries/{entryId}/reversal reverses an entry; the only request field is reason.
- GET /v1/entries lists entries.

⟦F4|The service exposes only the endpoints listed in this API section.⟧ The old in-process helper functions (post_raw and friends) are removed and nothing is expected to call them any more.

## Behavior notes

⟦F2|ledger-core exposes the list and search calls over entries by account, date range and reference, and returns them newest first.⟧ Pagination is unchanged from v1: clients pass a page token and receive at most a fixed page of entries.

Entry posting is idempotent on the reference field. Posting the same reference twice returns the original entry instead of creating a duplicate, which was the single most requested fix in the v1 retro. Currency conversion is still done by the callers; the ledger rejects entries whose two sides are not in the same currency.

## Deployment

⟦F1|ledger-core is deployed as three replicas behind the internal load balancer and starts with the usual platform bootstrap.⟧ Rolling updates replace one replica at a time. Health checks use the same readiness conventions as the other platform services (stale reference: the old name "ledger-svc" still appears in two dashboards and will be renamed).

## Security delta

Most v1 properties carry over unchanged, so only the points that changed shape are listed here.

- ⟦S:CRYPTO-05|Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.⟧
- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are written to the logs.⟧
- ⟦S:OPS-01|CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧

Transport: ⟦F3|all traffic to ledger-core is served over HTTPS only.⟧ Clients that used the in-process call path need no change on their side except the base URL.

## Cutover

Cutover happens per account range. Entries posted during the migration window are written to both stores, reconciled nightly, and the old tables are switched to read-only once two clean reconciliations in a row are done. If reconciliation reports a mismatch, the range stays on v1 and the team investigates before trying again (see runbook, link TBD).

## Open items

- Name of the new topic partition key (account or entry id?).
- Whether the balance endpoint should cache for one second.
- Decommission date of the old tables. Planned for the quarter after cutover, but the date is not fixed.
