# card token vault: infra tables

see also wiki "vault v1" (page moved, link dead)

## Components

| Component | Kind | Role |
|---|---|---|
| tokenization-service | service | tokenize / detokenize |
| vault-db (PostgreSQL) | database | encrypted card records + token mapping |
| Vault and KMS | secret store | data keys, runtime secrets |
| vault private subnet | network | boundary around the above |

## Terraform resources

| Resource | Name | Purpose |
|---|---|---|
| kms | vault_key | root key |
| rds | vault_db | card database |
| sg | vault_db_sg | database ingress |
| loggroup | vault_audit | audit trail |
| backup_vault | vault_backups | database backups |
| iam | vault_service_policy | service role permissions |

## Flows

| From | To | Data |
|---|---|---|
| Payment services | tokenization-service | PANs to tokenize, tokens to detokenize |
| tokenization-service | vault-db | encrypted card data |
| tokenization-service | Vault and KMS | data encryption key requests |

## Database

| Topic | Statement |
|---|---|
| Content | ⟦F2|vault-db (PostgreSQL) holds the encrypted card records and the token mapping.⟧ |
| Reachability | The database accepts connections only from the application subnet. |
| Service role | The service role can only read its own table. |
| Queries | ⟦S:API-05|All queries use bound parameters instead of string concatenation.⟧ |

## Access

| Topic | Statement |
|---|---|
| Internal calls | ⟦S:AUTH-02|Calls from payment services to the tokenization-service are authenticated with mutual TLS or signed workload identity tokens.⟧ |
| Tokens | ⟦S:AUTH-03|Tokens are short-lived (15 minutes maximum) and refresh tokens are single-use, so each refresh issues a new one.⟧ |
| Test data | ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧ |

⟦S:AUTHZ-01|Each request for a customer's resource checks that the caller owns it or is entitled to it.⟧
⟦S:LOG-02|Log lines are kept free of secrets, card numbers and personal details, and identifiers are opaque.⟧
⟦S:DATA-03|Before personal data is shared with a third party, an approved DPA must be in place, and we send just the fields needed.⟧
⟦S:DATA-02|Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.⟧
⟦S:AUTHZ-04|Debug and administrative routes are not exposed to the internet.⟧
⟦S:DATA-05|Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.⟧
⟦S:AUTHZ-03|Database credentials are per service with least-privilege grants, and no shared admin account is used by the application.⟧
⟦S:API-01|External inputs are accepted only if they validate against the schema.⟧
⟦S:LOG-04|Reading centralized logs requires authorization, and only approved staff have it.⟧
⟦S:API-04|The API returns sanitized errors with no stack traces, SQL fragments or internal hostnames.⟧

## Cryptography

| Topic | Statement |
|---|---|
| PANs | ⟦S:CRYPTO-02|Card numbers are never stored in clear text; they are replaced by tokens from the card token vault.⟧ |
| In transit | ⟦S:CRYPTO-04|Traffic between services, and between services and data stores or brokers, is encrypted in transit.⟧ |
| Keys | ⟦S:CRYPTO-06|Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year.⟧ |
| Certificates | ⟦F1|The client library is configured to ignore certificate errors after a failed deployment.⟧ |

## Secrets

| Topic | Statement |
|---|---|
| In artifacts | ⟦S:SECRET-01|Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.⟧ |
| At runtime | ⟦S:SECRET-02|At startup the service fetches its secrets from the approved secret store.⟧ |

## Network and callbacks

| Topic | Statement |
|---|---|
| Egress | ⟦S:NET-04|Third-party calls leave through an egress allowlist, not through open outbound access.⟧ |
| Callbacks | ⟦S:API-03|Every webhook we send or receive is signed with an HMAC, and the receiver checks the signature together with the timestamp.⟧ |

## Logging

| Topic | Statement |
|---|---|
| Security events | ⟦S:LOG-01|The audit trail includes authentication failures, privilege changes and sensitive-data access.⟧ |

## Backups and build

| Topic | Statement |
|---|---|
| Backups | Backups are encrypted. |
| Pipeline | ⟦F3|Container images are never rescanned after the first build.⟧ |
| Containers | ⟦S:OPS-02|No container runs as root, and the root filesystem is read-only wherever possible.⟧ |

## Sizing

| Metric | Value |
|---|---|
| Peak tokenize rate | a few hundred per second at month end |
| Detokenize rate | about half of tokenize |
| Regional recovery objective | four hours |
| Deployment | rolling, one instance at a time |

# Reference material for the token service

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

# Part 2: Reference material for the payment flows

This second part collects the functional details that the team keeps asking for. It does not change the decisions of the first part.

## 9. Payment lifecycle in detail

A payment passes through a fixed set of statuses. The table shows every allowed change and what triggers it.

| From | To | Trigger |
|---|---|---|
| (new) | authorized | the acquirer approves the amount |
| (new) | declined | the acquirer refuses the amount |
| (new) | pending | the acquirer does not answer within three seconds |
| pending | authorized | a late approval arrives |
| pending | declined | the retries are used up |
| authorized | captured | the merchant captures the full or a partial amount |
| authorized | expired | seven days pass without a capture |
| captured | partially_refunded | a refund smaller than the captured amount is booked |
| captured | refunded | refunds add up to the captured amount |
| partially_refunded | refunded | the remaining amount is refunded |

No other change is allowed. A request that asks for a change outside the table gets the answer `invalid_state` and nothing is stored. The status `expired` is final. When a merchant captures a payment after it has expired, the answer is `invalid_state`, and the merchant has to create a new payment.

### Partial captures

A merchant may capture less than the authorized amount. The difference is released after the capture, so the customer sees only the captured amount on the statement. A second capture on the same payment is not possible in the first release. Merchants that ship an order in several parcels ask for it often; the product team has it on the list for the next release.

Example: a payment of 120.00 EUR is authorized. The merchant ships the first parcel and captures 80.00 EUR. The payment is `captured` with the captured amount 80.00 EUR, and the remaining 40.00 EUR is released. If the customer then returns an item worth 25.00 EUR, the merchant requests a refund of 25.00 EUR, and the payment becomes `partially_refunded`.

## 10. Amounts and currencies

Amounts are whole numbers in the smallest unit of the currency. The number of decimals depends on the currency.

| Currency | Decimals | Example | Stored value |
|---|---|---|---|
| EUR | 2 | 12.34 | 1234 |
| GBP | 2 | 7.05 | 705 |
| SEK | 2 | 99.90 | 9990 |
| JPY | 0 | 1500 | 1500 |
| KWD | 3 | 4.250 | 4250 |

The currency of a payment is the currency of the merchant account. Conversion between currencies is not part of the first release; a merchant with an account in EUR cannot accept GBP. The currency code is always three capital letters according to ISO 4217. A request with a code that is not on the list of supported currencies gets the answer `unsupported_currency`.

Rounding is needed only for fees. The fee of a payment is calculated from the captured amount with the percentage of the merchant plan, rounded half up to the smallest unit, plus the fixed part of the plan. The fee is not part of the payment record; it is calculated again by the settlement module.

## 11. Routing to acquirers

Each merchant account is connected to one primary acquirer and, optionally, one fallback. The Acquirer connector chooses the acquirer by these rules, in this order:

1. If the card scheme of the payment is not supported by the primary acquirer, the fallback is used.
2. If the amount is above the limit of the primary acquirer, the fallback is used.
3. If the primary acquirer answered with a technical error three times in the last minute, the fallback is used for the next five minutes.
4. Otherwise the primary acquirer is used.

The card scheme is derived from the first digits of the card. The connector keeps a small table of ranges that is updated by the operations team once a month. If no range matches, the payment is declined with the reason `scheme_not_supported`.

### Acquirer limits

| Acquirer | Maximum per payment | Maximum per day and merchant |
|---|---|---|
| Acquirer A | 15,000.00 EUR | 250,000.00 EUR |
| Acquirer B | 10,000.00 EUR | 150,000.00 EUR |
| Acquirer C | 5,000.00 EUR | 80,000.00 EUR |

The limits are taken from the contracts and are configuration values, not code. When a limit changes, the operations team updates the configuration, and the change is applied by the connector within a minute.

## 12. The events of the payment-events topic

Every change of a payment is published as an event. All events have the same envelope.

| Field | Type | Example |
|---|---|---|
| event_id | string | evt_8f3a21 |
| event_type | string | payment.captured |
| occurred_at | timestamp | 2026-03-14T09:21:07Z |
| payment_id | string | pay_0042c9 |
| merchant_id | string | mer_1187 |
| status | string | captured |
| amount | integer | 8000 |
| currency | string | EUR |

The event types are `payment.authorized`, `payment.declined`, `payment.captured`, `payment.expired`, `payment.refunded` and `payment.partially_refunded`. Events of one payment are published in order, because the payment id is the key of the Kafka partition. Consumers must expect that an event can be delivered more than once and must use the event id to recognize repeats.

### Consumers

- The ledger service books the movement of money for `captured` and `refunded`.
- The notification service sends messages to merchants for `declined` and `refunded`.
- The reporting jobs read all events once a day and fill the tables of the finance team.

## 13. Reconciliation with the acquirers

Every night the acquirers send a settlement file. The gateway reads the file and compares each line with its own records. A line is matched by the acquirer message id. There are four outcomes: the line matches exactly, the amount differs, the line has no payment on our side, or a payment of ours has no line. The first outcome is the normal one and needs no action. The other three are written into the exception table, and the finance team works through it in the morning.

In the first three months of the pilot, the share of lines that matched exactly was 99.6 percent. Most exceptions came from payments that were captured late in the evening and appeared in the file of the next day. The team added a tolerance of one day for these cases.

## 14. Capacity and performance

The expected volume for the first year is 1.2 million payments per month, with peaks of 40 payments per second on the last Friday of the month. The service is dimensioned for 120 payments per second so that a failed instance does not cause delays.

| Operation | Median | 95th percentile |
|---|---|---|
| create payment | 640 ms | 1,400 ms |
| read payment | 18 ms | 45 ms |
| capture | 410 ms | 900 ms |
| refund | 380 ms | 850 ms |
| list payments (page of 50) | 60 ms | 140 ms |

The long time of the create call is the time of the acquirer. The gateway itself needs about 40 ms. The list call reads from an index on merchant and creation time.

## 15. Test plan

The tests follow the lifecycle table. For each allowed change there is a test that drives the payment into the start status, triggers the change and checks the new status, the stored record and the published event. For each forbidden change there is a test that expects `invalid_state`. A third group of tests uses the acquirer simulator, which can answer with approval, refusal, delay and technical error.

The contract tests compare the answers of the new service with the answers of the monolith for 400 recorded requests. The tests fail on any difference in field names, types or status codes. A short list of known differences is kept in the repository and reviewed in each release.

## 16. Release history and plan

| Version | Content | Date |
|---|---|---|
| 0.1 | create and read | month 1 |
| 0.2 | capture, partial capture | month 2 |
| 0.3 | refunds | month 3 |
| 0.4 | list endpoint, events | month 4 |
| 1.0 | pilot merchants | month 5 |
| 1.1 | all new merchants | month 6 |
| 1.2 | existing merchants in groups | months 7 to 9 |

## 17. Glossary

- **Authorization**: the approval of an amount by the acquirer; it reserves the amount on the card of the customer.
- **Capture**: the instruction to turn an authorization into a claim for money.
- **Refund**: giving money back to the customer after a capture.
- **Acquirer**: the bank that processes the card payments of a merchant.
- **Settlement**: the payout of the captured amounts, less fees, to the merchant.
- **Scheme**: the card network, for example Visa or Mastercard.
- **Minor unit**: the smallest unit of a currency, for example the cent.

## 18. Questions that integrators ask

**Can I capture more than I authorized?** No. The answer is `amount_exceeds_authorization`.

**How long is an authorization valid?** Seven days. After that the payment is `expired`.

**Why is my payment `pending`?** The acquirer did not answer in time. Wait for the event or read the payment again after a minute.

**Can I refund after a partial capture?** Yes, up to the captured amount.

**Do you send the events in order?** For one payment, yes. Events of different payments can overtake each other.

**What happens at the daylight saving change?** All timestamps are in UTC, so nothing happens.

# Appendix 2: related system, Notification Service; reference material for notifications

## Message model

A notification is one message to one recipient over one channel. It is created from an event or by a direct call, rendered from a template and handed to the provider.

| Field | Meaning | Example |
|---|---|---|
| id | identifier of the notification | ntf_90417 |
| channel | email, sms or push | sms |
| recipient_id | the customer or merchant who receives it | cus_30481 |
| template_id | the template that was used | tpl_transfer_received |
| locale | language and region of the message | de-DE |
| status | queued, sent, delivered, failed | delivered |
| created_at | creation time, UTC | 2026-04-02T07:02:11Z |

### Status changes

| From | To | Trigger |
|---|---|---|
| queued | sent | the provider accepts the message |
| sent | delivered | the provider reports delivery |
| queued | failed | the retries are used up |
| sent | failed | the provider reports a permanent failure |

## Templates

Templates are plain text with placeholders in double curly braces. A template has a subject (for email and push) and a body. For every template there is one version per locale. The English version is the fallback.

| Template | Event | Channels |
|---|---|---|
| tpl_transfer_received | wallet.transfer_in | push, sms |
| tpl_payment_declined | payment.declined | email |
| tpl_refund_issued | payment.refunded | email |
| tpl_statement_ready | statement.created | email |
| tpl_topup_failed | wallet.topup_failed | push |

Placeholders are filled from the event: the amount, the currency, the name of the merchant, the date. The notifier formats amounts and dates according to the locale of the recipient. For example, the amount 1234.50 EUR is shown as `1.234,50 €` for `de-DE` and as `€1,234.50` for `en-IE`.

### Template changes

A template is changed through the template endpoint. The change is valid for new messages immediately. The previous version stays in the history, so that the team can see which text a customer received at a given time.

## Choosing the channel

The channel comes from the event type and the preference of the recipient. Each event type has a default channel and a list of allowed channels. The preference of the customer may select any allowed channel. If the chosen channel fails permanently, the notifier does not switch to another channel; the status is `failed` and the producing team decides whether to send again.

## Merging

Messages to the same recipient for the same event type within one minute are merged into one. The merged message uses the template of the event type and lists the amounts one under another. The merge window is a configuration value per event type; transfers use 60 seconds, statements use none.

## Delivery numbers from the pilot

| Channel | Messages | Delivered within 1 minute | Failed |
|---|---|---|---|
| push | 412,000 | 97.2 percent | 0.4 percent |
| sms | 188,000 | 95.1 percent | 1.1 percent |
| email | 305,000 | 91.8 percent | 0.9 percent |

Email deliveries are slower because the providers of the recipients queue messages. The team does not count an email as late if it is delivered within ten minutes.

## Capacity

The notifier processes about 600 thousand messages per day at the start and is dimensioned for 3 million. Peaks occur at 08:00 and 18:00 local time, when scheduled messages are sent.

| Operation | Median | 95th percentile |
|---|---|---|
| render a message | 4 ms | 11 ms |
| hand over to the provider | 120 ms | 450 ms |
| read a status | 9 ms | 24 ms |
| replace a template | 18 ms | 40 ms |

## Migration of the old modules

| Module | Event types | Step | Parallel run |
|---|---|---|---|
| payments | payment.declined, payment.refunded | 1 | two weeks |
| wallet | wallet.transfer_in, wallet.topup_failed | 2 | two weeks |
| statements | statement.created | 3 | two weeks |
| reminders | reminder.due | 4 | two weeks |

During the parallel run the old module also sends. A comparison job lists messages that were sent by one side only.

## Glossary

- **Channel**: the way a message reaches the recipient.
- **Template**: the text of a message with placeholders.
- **Placeholder**: a field in double braces that the notifier fills.
- **Locale**: the combination of language and region.
- **Merge window**: the time within which similar messages are combined.

## Questions of the producing teams

**How do I add a new event type?** Register it with the platform team together with the template for each channel and locale.

**Can I send a message without an event?** Yes, through the notification endpoint.

**What is the maximum length of an SMS?** 160 characters for one part; longer messages are split into parts of 153 characters.

**What if the template is missing for the locale?** The English template is used and the fallback is recorded.
