fraud scoring - slack paste

**scoring-engine** reads payment events from payment-events (MSK), scores them and writes the decision to decisions-db (PostgreSQL). model is a file loaded every 15 min.

**nightly** The scoring-engine also has a nightly job that refreshes the feature tables.

**ops stuff**
- Balances reconciled with the ledger every day, difference of more than 0.01 EUR reported to the finance team within 24 hours.
- Replaced API versions kept 12 months, removal announced 90 days in advance.
- Processed messages deleted from payment-events.
- Support agents see card numbers and document numbers only masked.

**limits**
Support agents change the limit of a customer on request, without anyone else.

**sandbox**
The sandbox is a copy of the production database in which only the names are changed.
