# Ledger Service Design

(Part 1 by Marek, part 2 by Ines)

## Part 1: What the ledger is (Marek)

The ledger is a double-entry book. Every movement of money is a balanced journal entry: debits equal credits. Wallet and payment services post entries; nobody changes an entry afterwards, a mistake is corrected by a reversal entry.

Components:
- ledger-core: validates and stores entries
- ledger-db (PostgreSQL): entries and balances
- ledger-events (Kafka): every posted entry is published for consumers

Endpoints:
- POST /v1/entries posts a balanced entry
- GET /v1/entries/{entryId} retrieves it
- GET /v1/accounts/{accountId}/balance gives the balance
- POST /v1/entries/{entryId}/reversal reverses an entry
- GET /v1/entries lists entries by filter

Posting is idempotent by the key sent by the caller. An entry that does not balance is rejected with 422.

## Part 2: Operations and obligations (Ines)

Large payments: ⟦F1|transactions above 10,000 EUR are put on hold, and held transactions that nobody has reviewed after 24 hours are released automatically so that the books are not blocked.⟧

Records: ⟦S:ARC-01|transaction records are kept for 7 years and deleted within 90 days after that.⟧

Components: ⟦S:VUL-01|Critical vulnerabilities are fixed in production within 7 days after publication.⟧

Test setups: ⟦S:TST-01|production data is not copied to test or development environments.⟧ ⟦F2|The ledger-core is also deployed in a staging setup for the partner integrations.⟧

Messages and exports: ⟦S:EXP-01|Exported files with personal data are encrypted and deleted from the download location after 7 days.⟧ ⟦S:EXP-02|Exports of more than 1,000 customer records need the written approval of the data owner.⟧

Register: ⟦S:INV-02|The register lists the personal data of the ledger and each third party that receives data.⟧

On call: ⟦S:MON-01|high alerts are acknowledged within 15 minutes.⟧

## Open questions

- should the reversal endpoint also accept a reason code?
