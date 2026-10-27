ledger service - sprint 14 design

WHAT: double-entry ledger. wallet + payments post balanced entries. no edits, only reversals.

PARTS
- ledger-core (service)
- ledger-db (postgres)
- ledger-events (kafka)

API
- POST /v1/entries
- GET /v1/entries/{entryId}
- GET /v1/accounts/{accountId}/balance
- POST /v1/entries/{entryId}/reversal
- GET /v1/entries

BEHAVIOR
- idempotency key from caller
- unbalanced entry -> 422
- events published after commit

RULES (ines made me write these)
- ⟦S:ARC-01|Records of transactions: 7 years, deleted within 90 days after.⟧
- ⟦S:VUL-02|Components never more than two major versions behind latest; versions in the register.⟧
- ⟦S:TST-01|No production data in test or development environments.⟧
- ⟦S:TST-02|Test accounts in production removed within 7 days after the test ends.⟧
- ⟦S:NTF-01|No card numbers, passwords or document images in messages to customers.⟧
- ⟦F1|Bulk exports of customer records are approved by the team lead before they run.⟧
- ⟦S:INV-01|Owner and deputy named in the service register.⟧
- ⟦S:FRD-01|Transactions above 10,000 EUR are held for review by the fraud team before settlement.⟧
- ⟦F2|The ledger-core entries are copied to the finance reporting database every night.⟧

NEXT SPRINT: pagination for GET /v1/entries
