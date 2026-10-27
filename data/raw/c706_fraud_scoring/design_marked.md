fraud scoring - slack paste

**scoring-engine** reads payment events from payment-events (MSK), scores them and writes the decision to decisions-db (PostgreSQL). model is a file loaded every 15 min.

**nightly** ⟦F3|The scoring-engine also has a nightly job that refreshes the feature tables.⟧

**ops stuff**
- ⟦S:REC-01|Balances reconciled with the ledger every day, difference of more than 0.01 EUR reported to the finance team within 24 hours.⟧
- ⟦S:VER-01|Replaced API versions kept 12 months, removal announced 90 days in advance.⟧
- ⟦S:MSG-02|Processed messages deleted from payment-events.⟧
- ⟦S:SUP-01|Support agents see card numbers and document numbers only masked.⟧

**limits**
⟦F1|Support agents change the limit of a customer on request, without anyone else.⟧

**sandbox**
⟦F2|The sandbox is a copy of the production database in which only the names are changed.⟧
