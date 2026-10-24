# PGW v2 - design (terse)

Everything below assumes the usual platform setup unless a line says otherwise.

## Scope

- Edge GW -> payments-core -> payments-db (PG) + acquirer connector + payment-events (Kafka).
- Merchant BE sends card token only; no PAN on our side except in the vault.

## API surface

- POST /v1/payments (amount, currency, card_token, merchant_id, reference) -> id, status, amount, currency, last4, merchant_id
- GET /v1/payments/{paymentId} -> same shape
- POST /v1/payments/{paymentId}/capture (amount) -> same shape
- POST /v1/payments/{paymentId}/refunds (amount, reason) -> id, status, amount
- GET /v1/payments -> list, same shape

## AuthN/Z

- ⟦S:AUTH-01|All external endpoints authenticate via OAuth2/OIDC bearer or mTLS.⟧
- ⟦S:AUTH-03|Access tokens max 15 min; refresh tokens rotated on use.⟧
- ⟦S:AUTH-06|The login and token endpoints throttle repeated failures and apply a temporary lockout once an account reaches ten consecutive failed attempts.⟧
- ⟦S:AUTHZ-03|The application never uses a shared administrative database login; it has a dedicated, minimally privileged account.⟧
- ⟦S:AUTHZ-01|Per-request ownership/entitlement check on every customer-owned resource.⟧
- ⟦S:AUTHZ-04|Admin and debug endpoints are reachable only from the internal network, not from the public internet.⟧

## Data

- ⟦S:CRYPTO-01|Encryption at rest with AES-256 covers personal data in databases and object storage, and its keys live in the corporate key management service.⟧
- ⟦S:CRYPTO-02|PANs never stored in clear and tokenized by the card token vault.⟧
- ⟦S:CRYPTO-06|Keys in KMS, never next to the data, rotated at least annually.⟧
- ⟦F1|Acquirer onboarding data and some merchant contact details go to the new fraud vendor under a verbal agreement with their account manager.⟧
- ⟦F2|When a payment bug is hard to reproduce, support analysts copy the real merchant and cardholder records into staging.⟧

## Transport / crypto

- ⟦S:CRYPTO-07|Outbound TLS validates certs, verification never disabled.⟧
- ⟦S:DATA-05|Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.⟧
- ⟦S:CRYPTO-05|Approved algs only; no MD5, SHA-1, DES, 3DES, ECB.⟧

## Network

- ⟦S:NET-01|DB and brokers private subnets, not publicly reachable.⟧
- ⟦S:NET-05|External APIs behind WAF with rate limiting.⟧
- ⟦S:AUTH-02|Calls between our own services carry a signed workload identity token or use mutual TLS, and the receiving service checks it.⟧
- ⟦S:NET-04|Egress for third-party callers restricted to approved allowlist.⟧
- ⟦S:LOG-02|Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.⟧

## Secrets

- ⟦S:SECRET-01|No secrets in code, config, specs or infra definitions.⟧
- ⟦S:SECRET-02|On boot, the service pulls its credentials from the approved secret store.⟧

## Logging

- ⟦S:LOG-01|Log auth failures, privilege changes, access to sensitive data.⟧

## App / ops

- ⟦S:API-01|External input validated against schema, invalid rejected.⟧
- ⟦S:API-03|Webhook payloads are HMAC-signed and timestamped, and the receiver verifies the signature and the timestamp before accepting them.⟧
- ⟦S:API-02|The API enforces a limit of 300 requests per minute for each client and answers HTTP 429 when it is exceeded.⟧
- ⟦S:API-04|Internal details such as stack traces, SQL and hostnames never appear in an error response.⟧
- ⟦S:API-05|Parameterized queries only.⟧
- ⟦S:DATA-02|Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.⟧
- ⟦S:CRYPTO-04|Connections to the database and between internal services use TLS.⟧
- ⟦S:OPS-01|CI scans deps and images; criticals fixed within 14 days.⟧
- ⟦S:OPS-02|Containers non-root, RO rootfs where possible.⟧
- ⟦S:LOG-04|Only authorized staff can access the central logs.⟧

## Behavior notes

- Authorize/capture split: capture <= authorized amount, partial capture allowed once.
- Refund: up to captured amount, multiple partials ok, async ack via event.
- Idempotency: reference + merchant_id unique; repeat returns original.
- Events: payment.authorized / captured / refunded / failed on payment-events, at-least-once.

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
