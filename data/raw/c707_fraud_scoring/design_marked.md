# Fraud Scoring - Operating Document

## Overview

The scoring-engine reads payment events from payment-events (MSK), computes a risk score and stores the decision in decisions-db (PostgreSQL). The audit output goes to the scoring audit log group. Decisions are allow, review or block.

## Commitments

- ⟦S:REC-01|Balances are reconciled with the ledger every day, and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.⟧
- ⟦S:REC-02|Differences found in a reconciliation are resolved within 5 working days.⟧
- ⟦S:LIM-01|The daily outgoing transfers of a customer are limited by the limit table, and a change of a limit needs the approval of a second employee.⟧
- ⟦S:VER-02|Breaking changes of the API are released only as a new version of the API.⟧
- ⟦S:SBX-01|The merchant sandbox contains only generated data and runs separately from production.⟧
- ⟦S:JOB-01|Every scheduled job runs with its own service account, which cannot log in interactively.⟧
- ⟦S:SUP-01|Support agents see card numbers and document numbers only in masked form.⟧
