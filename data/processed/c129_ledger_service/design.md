# Ledger service: topology narration

## Topology

Read the picture left to right. The wallet and payment services submit journal entries to **ledger-core**. ledger-core validates that debits equal credits, writes the entry to **ledger-db (PostgreSQL)** inside one transaction, and publishes a posted-entry event to **ledger-events (Kafka)** after the commit. Consumers of the events, such as reporting and notifications, read the stream.

```
 [Wallet and payment services]
              |
              | journal entries
              v
     +-------------------+   entries, balances   +------------------------+
     |    ledger-core    |---------------------->| ledger-db (PostgreSQL) |
     +-------------------+                       +------------------------+
              |
              | posted entry events
              v
     +-------------------+
     |  ledger-events    |
     |     (Kafka)       |
     +-------------------+
```

Edges:

1. Wallet and payment services -> ledger-core: journal entries and balance queries.
2. ledger-core -> ledger-db (PostgreSQL): entries and balances.
3. ledger-core -> ledger-events (Kafka): posted entry events.

ledger-core processes each journal entry in one database transaction and writes the posted-entry event to ledger-events (Kafka) after the commit.

## API inventory

| operation | method and path | purpose |
|---|---|---|
| postEntry | POST /v1/entries | post a balanced journal entry |
| getEntry | GET /v1/entries/{entryId} | retrieve an entry |
| getBalance | GET /v1/accounts/{accountId}/balance | get account balance |
| reverseEntry | POST /v1/entries/{entryId}/reversal | reverse an entry |
| listEntries | GET /v1/entries | list entries |

Reversal is implemented as a normal posting with the debit and credit accounts swapped and a link to the original entry. Entries are never edited or deleted.

## Control surface

Identity and access:
- Authentication between the internal services is considered for later, and for now the services that consume the ledger events read them without any credentials.
- All state-changing operations require an authenticated caller.
- Internal users receive only the roles required for their job; roles are defined per service.
- Access rights to production systems are reviewed at least quarterly.

Cryptography and secrets:
- Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.

Network, logging and code:
- The database and the message brokers sit in private subnets and are not publicly reachable.
- Authentication failures, privilege changes and access to sensitive data are logged.
- Database queries are parameterized; concatenating user input into queries is prohibited.

## Behavior notes

Balances are computed from entries and cached for one second under heavy read load. Posting the same reference twice returns the first entry. The posted-entry event carries the entry id and not the amounts, so consumers read the entry from the API when they need details.
