# LED-100: Ledger Service release 1

**Type:** Epic  **Priority:** High  **Component:** ledger  **Reporter:** Platform Finance

## Description

First release of the Ledger Service, the double-entry ledger of the platform. It is consumed by the wallet and payment services over the private network; there are no external callers.

## User stories

**LED-101** As a service, I want to post a balanced journal entry.
Acceptance criteria:
1. POST /v1/entries accepts debit_account, credit_account, amount, currency and reference.
2. The response returns id, debit_account, credit_account, amount and posted_at.
3. A second call with the same reference returns the first entry.

**LED-102** As a service, I want to read an entry.
Acceptance criteria:
1. GET /v1/entries/{entryId} returns id, debit_account, credit_account, amount and posted_at.

**LED-103** As a service, I want to read the balance of an account.
Acceptance criteria:
1. GET /v1/accounts/{accountId}/balance returns account_id, balance and currency.

**LED-104** As a service, I want to reverse an entry.
Acceptance criteria:
1. POST /v1/entries/{entryId}/reversal accepts a reason and posts a mirror entry.
2. The response returns the new entry with the same five fields.

**LED-105** As an accountant, I want to list entries.
Acceptance criteria:
1. GET /v1/entries returns the entries in pages with the same five fields.

## Non-functional requirements

**LED-110** Change.
Acceptance criteria:
1. Every change to production has a rollback plan that has been tested in a pre-production environment.

**LED-111** Delivery.
Acceptance criteria:
1. The pipeline stores its credentials as variables of the pipeline project, and all developers can read them.
2. Build artifacts are signed, and the signature is verified before deployment.

**LED-112** Money safety.
Acceptance criteria:
1. Every feature that moves money has a kill switch, and the kill switch is tested every quarter.

**LED-113** Dashboard.
Acceptance criteria:
1. A dashboard shows the number of posted entries per minute and the number of reversals per day.
2. Nobody has checked that the numbers on the dashboard are right.

## Rollout

LED-120: the release serves the wallet service first (see LED-050 for the migration of the balances). The payment service follows after one week without a mismatch in the reconciliation (TBD).

## Open

LED-130: retention of the entries (TBD). LED-131: second currency for the reversal (TBD).
