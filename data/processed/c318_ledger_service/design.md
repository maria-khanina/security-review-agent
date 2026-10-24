# Ledger service

## Components

| Component | Kind | Role |
|---|---|---|
| ledger-core | service | posts entries, answers balances |
| ledger-db | PostgreSQL | entries, balances |
| ledger-events | Kafka | posted-entry events |

## Flows

| From | To | Data |
|---|---|---|
| Wallet and payment services | ledger-core | journal entries |
| ledger-core | ledger-db | entries, balances |
| ledger-core | ledger-events | posted-entry events |

## Endpoints

| Method | Path | Request | Response |
|---|---|---|---|
| POST | /v1/entries | debit_account, credit_account, amount, currency, reference | id, debit_account, credit_account, amount, posted_at |
| GET | /v1/entries/{entryId} | - | same as above |
| GET | /v1/accounts/{accountId}/balance | - | account_id, balance, currency |
| POST | /v1/entries/{entryId}/reversal | reason | cancelling entry |
| GET | /v1/entries | - | list of entries |

## Behavior

| Topic | Rule |
|---|---|
| Balance | sum of the account's entries, never stored |
| Currency | both sides must match, else rejected |
| Idempotency | same reference returns the original entry |
| Reversal | cancelling entry, once per entry |
| Roles | ledger-core applies the roles of its callers and of the finance users to every call. |

## Access and keys

| Topic | Statement |
|---|---|
| Internal calls | Service-to-service calls are authenticated, either with mutual TLS between the workloads or with a signed workload identity token. |
| Tokens | A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use. |
| Keys | KMS holds the keys, the data stores only keep ciphertext, and key rotation happens at least yearly. |

Nothing administrative or meant for debugging can be called from outside our network.
Error responses do not expose stack traces, SQL or internal hostnames.
Reading centralized logs requires authorization, and only approved staff have it.

## Transport and crypto

| Topic | Statement |
|---|---|
| Internal traffic | Traffic between services, and between services and data stores or brokers, is encrypted in transit. |
| Algorithms | We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode. |
| Certificates | Outbound TLS connections always verify the peer certificate. |

## Secrets and network

| Topic | Statement |
|---|---|
| In artifacts | No secrets are kept in source code, config files, API specs or infrastructure definitions. |
| At runtime | The approved secret manager is the only source of runtime secrets, fetched at start-up. |
| Placement | ledger-db and the Kafka brokers sit in private subnets and are not publicly reachable. |
| Egress | The service can reach only allow-listed third-party hosts, and all other outbound traffic is blocked. |

## Logging, data, code, ops

| Topic | Statement |
|---|---|
| Security events | The audit trail includes authentication failures, privilege changes and sensitive-data access. |
| Test data | Non-production environments do not contain real personal or card data. |
| Callbacks | Inbound and outbound webhooks include an HMAC signature and a timestamp; verification of both is mandatory on the receiving side. |
| Queries | Database queries are parameterized, and user input is never concatenated into SQL. |
| Pipeline | Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less. |
| Containers | The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only. |

## Reconciliation

| Item | Value |
|---|---|
| Job | nightly, after midnight UTC |
| Check | sum of entries equals sum of balances |
| On difference | page the finance engineer on call |

# Reference material for the ledger

## Chart of accounts

Accounts are grouped into classes by the first digit of the number. The classes follow the usual double-entry layout.

| Class | Meaning | Examples |
|---|---|---|
| 1 | assets | 1100 customer funds, 1200 funds at acquirers |
| 2 | liabilities | 2100 wallet balances, 2200 merchant payables |
| 3 | equity | 3100 retained result |
| 4 | income | 4100 payment fees, 4200 payout fees |
| 5 | expenses | 5100 acquirer fees, 5200 refunds written off |

Every wallet has its own account in class 2, every merchant its own account in class 2, and the platform accounts in the other classes are shared. Account numbers have the form `class-group-id`, for example `2100-0001-5521`.

## Entry model

An entry moves one amount from a debit account to a credit account. The amount is a positive whole number in minor units. Complex bookings use several entries with the same booking reference.

| Field | Meaning |
|---|---|
| id | identifier of the entry |
| debit_account | account that is debited |
| credit_account | account that is credited |
| amount | positive whole number in minor units |
| currency | ISO 4217 code |
| reference | text that links the entry to the business event |
| posted_at | time of posting, UTC |

### Posting rules

- Debit and credit accounts must differ.
- Both accounts must exist and be open.
- The currency of the entry must be the currency of both accounts.
- An entry is posted exactly once; the posting time is set by the ledger.
- Entries are never changed and never removed.

## Typical bookings

**Capture of a card payment of 100.00 EUR with a fee of 1.50 EUR.**

| Entry | Debit | Credit | Amount |
|---|---|---|---|
| 1 | 1200 funds at acquirers | 2200 merchant payable | 10000 |
| 2 | 2200 merchant payable | 4100 payment fees | 150 |

**Wallet transfer of 15.50 EUR.**

| Entry | Debit | Credit | Amount |
|---|---|---|---|
| 1 | 2100 wallet of the sender | 2100 wallet of the receiver | 1550 |

**Reversal of the transfer.** The reversal is a new entry with debit and credit swapped and a reference to the original entry. The original stays in the ledger.

## Balances

The balance of an account is the sum of its credits minus the sum of its debits for accounts of class 2, 3 and 4, and the opposite for classes 1 and 5. The ledger keeps a running balance with each account to avoid summing all entries on every read. The nightly check compares the running balances with the sums.

## Events

Each posted entry is published to the ledger-events topic. The event holds the entry id, the accounts, the amount, the currency, the reference and the posting time. Consumers are the reporting jobs, the notification service and the finance team's export. Events of one account are published in order.

## Capacity

| Measure | Value at start | Dimensioned for |
|---|---|---|
| entries per day | 1.1 million | 5 million |
| entries per second at peak | 60 | 300 |
| accounts | 2.4 million | 8 million |

| Operation | Median | 95th percentile |
|---|---|---|
| post an entry | 22 ms | 60 ms |
| read an entry | 8 ms | 20 ms |
| read a balance | 6 ms | 15 ms |
| list entries (page of 100) | 30 ms | 75 ms |
| reversal | 28 ms | 70 ms |

## Month-end

On the last working day of the month the finance team closes the period. The close runs these steps in order: the ledger stops accepting entries dated in the closing period, the nightly check runs, the reporting jobs produce the trial balance, and the finance team signs the result. Entries for the closed period are booked in the next period with a reference to the original date.

## Migration from the old module

| Step | Content | Check |
|---|---|---|
| 1 | copy the chart of accounts | numbers equal |
| 2 | copy opening balances | sums equal per class |
| 3 | post in parallel for one month | daily comparison of balances |
| 4 | switch readers to the new service | reports equal |
| 5 | archive the old tables | none |

## Glossary

- **Debit** and **credit**: the two sides of an entry.
- **Posting**: writing an entry to the ledger.
- **Reversal**: a new entry that cancels the effect of an earlier one.
- **Trial balance**: the list of all account balances at a date.
- **Period**: a month for which the books are closed.

## Questions of the finance team

**Can an entry be deleted?** No. A mistake is reversed and the right entry is posted.

**Why does the balance of a merchant payable change after a refund?** A refund is posted as a debit of the merchant payable and a credit of funds at acquirers.

**Which time zone has the posting time?** UTC; the reports convert to the time zone of the reader.

**Can two entries have the same reference?** Yes; a business event can need several entries.

# Appendix 1: related system, Card Token Vault; reference material for the token service

## Token format

A token is a string of the form `tok_` followed by 24 characters from the alphabet of lower-case letters and digits. The characters are random and carry no information about the card. Two tokens never collide: the service checks the new token against the existing ones before it returns it.

| Property | Value |
|---|---|
| prefix | tok_ |
| length | 28 characters |
| alphabet | a to z and 0 to 9 |
| example | tok_4k2m9c0q7v1x8d3b6n5a2h0y |

The same card number always gives the same token for the same merchant. A different merchant gets a different token for the same number. This lets a merchant recognize a returning card without learning anything about the number.

## Operations in detail

**Tokenize.** The caller sends a card number, the expiry month and year, and the merchant id. The service checks the format of the number with the Luhn rule and the length for the scheme, creates or finds the token and returns it together with the last four digits and the scheme.

**Detokenize.** The caller sends a token. The service returns the card number, the expiry and the scheme.

**Lookup by last four digits.** Support tools can ask for the tokens of a merchant that end in four given digits. The answer lists tokens and expiry dates, never numbers.

### Answers

| Answer | Meaning |
|---|---|
| 200 | the operation succeeded |
| 400 invalid_number | the number fails the Luhn rule or has the wrong length |
| 400 invalid_expiry | the expiry date is in the past or malformed |
| 404 unknown_token | the token does not exist |
| 503 unavailable | the service cannot reach its database |

## Card schemes

The scheme is derived from the first digits of the number.

| Scheme | First digits | Length |
|---|---|---|
| Visa | 4 | 13 or 16 |
| Mastercard | 51 to 55, 2221 to 2720 | 16 |
| American Express | 34, 37 | 15 |
| Maestro | 50, 56 to 69 | 12 to 19 |

The table is configuration. When a scheme adds a range, the operations team changes the configuration and the service applies it within a minute.

## Capacity

The service holds about forty million card records today and grows by about five million per year.

| Operation | Median | 95th percentile |
|---|---|---|
| tokenize | 12 ms | 28 ms |
| detokenize | 15 ms | 34 ms |
| lookup by last four digits | 20 ms | 55 ms |

The service is dimensioned for two thousand calls per second at peak. The load tests of the last quarter reached three thousand calls per second without errors; the average load is 240 calls per second, and the peak on the last Friday of the month is 900.

## Callers and volumes

| Caller | Share of calls | Main operation |
|---|---|---|
| payment gateway | 61 percent | tokenize at payment creation |
| refund service | 18 percent | detokenize for refunds to cards |
| wallet service | 14 percent | tokenize for card top-ups |
| support tools | 7 percent | lookup by last four digits |

## Migration of the old card store

The old card store of the monolith contains the same number of records. The migration copies them in batches of 50 thousand records per night. After each batch, the service compares a random sample of 1,000 records with the old store. The migration is complete when the number of records is equal and the last three samples match completely. The old store is switched to read-only on the day of the last batch, and removed one month later.

## Glossary

- **Token**: a random string that stands for a card number.
- **Scheme**: the card network.
- **Luhn rule**: the check digit rule for card numbers.
- **Merchant id**: the identifier of the merchant for whom a token is made.
- **Batch**: a group of records copied in one step of the migration.

## Questions of the integrating teams

**Can I compare two tokens of different merchants?** No, they differ for the same card.

**Does a token expire?** No. A token stays valid as long as the card record exists.

**What happens when a card is replaced by the bank?** The customer adds the new card, and it gets a new token.

**How do I get the scheme of a token?** It is returned by the tokenize call, together with the last four digits.

# Appendix 2: related system, Refund Service; reference material for refunds

## Refund model

A refund returns money from a captured payment to the customer. It belongs to exactly one payment and has its own lifecycle.

| Field | Meaning | Example |
|---|---|---|
| id | identifier of the refund | ref_3304 |
| payment_id | the payment that is refunded | pay_0042c9 |
| amount | refunded amount in minor units | 2500 |
| currency | ISO 4217 code | EUR |
| reason | reason code | goods_returned |
| requested_by | the person or system that asked | agent_218 |
| status | requested, approved, rejected, executed, cancelled, failed | executed |
| created_at | time of the request, UTC | 2026-03-18T13:41:55Z |

### Reason codes

| Code | Meaning |
|---|---|
| goods_returned | the customer returned the goods |
| service_not_delivered | the service was not delivered |
| duplicate_payment | the customer paid twice |
| price_adjustment | the merchant lowers the price afterwards |
| goodwill | the merchant refunds without a claim |
| other | free text in the comment field |

## Rules for amounts

- The amount of one refund must be positive and not larger than the captured amount of the payment minus earlier refunds.
- The currency of the refund must be the currency of the payment.
- A refund can be requested up to 180 days after the capture.
- A payment can have at most 20 refunds.

A request that breaks a rule gets the answer `refund_not_allowed` with the name of the rule.

## Statuses

| From | To | Trigger |
|---|---|---|
| requested | approved | the approving person accepts |
| requested | rejected | the approving person refuses |
| requested | cancelled | the requester withdraws the request |
| approved | executed | the payment gateway confirms the refund |
| approved | failed | the confirmation does not arrive after five retries |

`executed`, `rejected`, `cancelled` and `failed` are final. A failed refund is handed to the operations team, which either repeats it by hand or contacts the merchant.

## Timing

The customer sees the money on the card statement after a time that depends on the bank. The gateway confirms the refund within seconds; the bank needs between three and ten working days.

| Step | Typical time |
|---|---|
| request to approval | 4 working hours |
| approval to execution | under 1 minute |
| execution to money on the statement | 3 to 10 working days |

## Volumes

The service handles about 9,000 refund requests per day at the start. About 62 percent of requests come from merchant backends, 38 percent from support agents.

| Reason | Share |
|---|---|
| goods_returned | 47 percent |
| duplicate_payment | 18 percent |
| service_not_delivered | 14 percent |
| price_adjustment | 9 percent |
| goodwill | 7 percent |
| other | 5 percent |

## Capacity

| Operation | Median | 95th percentile |
|---|---|---|
| request a refund | 85 ms | 200 ms |
| read a refund | 14 ms | 35 ms |
| list refunds (page of 50) | 40 ms | 95 ms |
| record a decision | 60 ms | 140 ms |
| cancel | 45 ms | 100 ms |

## Events

Each change of status is published to refund-events with the refund id, the payment id, the old and the new status and the time. The consumers are the ledger, the notification service and the reporting jobs.

## Reports for the finance team

The finance team receives a daily table of refunds by reason, merchant and status, and a weekly table of the refund rate per merchant, which is the share of the captured amount that was refunded. Merchants with a refund rate above five percent are listed for the commercial team.

## Release plan

| Phase | Users | Duration |
|---|---|---|
| 1 | support agents | one month |
| 2 | merchants in groups of fifty | three months |
| 3 | switch-off of the old module | one month after the last group |

## Glossary

- **Refund**: money returned to the customer after a capture.
- **Reason code**: the standard explanation of a refund.
- **Refund rate**: the share of captured money that is refunded.
- **Final status**: a status that never changes again.

## Questions of the merchants

**Can I refund more than the payment?** No, the answer is `refund_not_allowed`.

**Can I cancel an executed refund?** No. A refund that was executed cannot be undone.

**How do I see why a refund failed?** The refund record has a failure reason; the support team can explain it.

**Is a partial refund possible?** Yes, any amount up to the remaining captured amount.
