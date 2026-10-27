# Fraud Scoring - Operating Document

## Overview

The scoring-engine reads payment events from payment-events (MSK), computes a risk score and stores the decision in decisions-db (PostgreSQL). The audit output goes to the scoring audit log group. Decisions are allow, review or block.

## Commitments

- Balances are reconciled with the ledger every day, and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.
- Differences found in a reconciliation are resolved within 5 working days.
- The daily outgoing transfers of a customer are limited by the limit table, and a change of a limit needs the approval of a second employee.
- Breaking changes of the API are released only as a new version of the API.
- The merchant sandbox contains only generated data and runs separately from production.
- Every scheduled job runs with its own service account, which cannot log in interactively.
- Support agents see card numbers and document numbers only in masked form.
