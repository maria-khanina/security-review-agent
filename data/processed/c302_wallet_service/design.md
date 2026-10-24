# wallet service: topology and notes

```
 [Mobile app]
      |  wallet + transfer requests
      v
 +---------------------+   token validation   +-----------+
 | Mobile API Gateway  |--------------------->|  Keycloak |
 +---------------------+                      +-----------+
      |  authenticated requests
      v
 +---------------------+   balances, txns   +--------------------+
 |    wallet-core      |------------------->| wallet-db (PG)     |
 +---------------------+                    +--------------------+
```

## API (as built)

- GET /v1/wallets/{walletId}: wallet + balance. Resp: id, owner_name, balance, currency.
- POST /v1/wallets/{walletId}/topups: top-up from funding source. Req: amount, funding_source_id. Resp: id, type, amount, created_at.
- POST /v1/transfers: wallet to wallet. Req: from_wallet_id, to_wallet_id, amount, note. Resp: same txn shape.
- GET /v1/wallets/{walletId}/transactions: txn list.
- PATCH /v1/wallets/{walletId}/profile: owner_name, phone_number, address.

The service exposes only the endpoints listed in the API section.

All state-changing operations require an authenticated caller.

## Boxes, one line each

- Gateway: single ingress, validates tokens against Keycloak, forwards to wallet-core. Mobile traffic only.
- wallet-core: balance math, transfer saga, idempotency on transfer reference.
- wallet-db (PostgreSQL) stores balances, transactions and the wallet owner profile.
- Keycloak: IdP for customers; realm per market.

## Auth and access

- Passwords in Keycloak's legacy import table are hashed with plain SHA-256 without a per-user salt, kept that way to avoid forcing a reset.

## Data

- Encryption at rest with AES-256 covers personal data in databases and object storage, and its keys live in the corporate key management service.
- Keys live in KMS, never next to the data, rotated at least annually.
- Personal data goes to third parties only under an approved DPA, only required fields.
- Non-prod environments hold no real personal or card data.
- Backups are copied to a separate account without encryption, which keeps cross-account restore trivial.

## Transport and edge

- Outbound TLS connections validate certificates; verification is never off.
- Approved algorithms only; MD5, SHA-1, DES, 3DES and ECB are banned.
- Each client is limited to 100 requests per minute, and requests above the limit receive HTTP 429.
- wallet-db sits in private subnets, no public endpoint.
- A WAF with rate limiting protects the externally exposed API.
- Tokens are short-lived (15 minutes maximum) and refresh tokens are single-use, so each refresh issues a new one.
- Egress to third parties is restricted to an approved allowlist.
- Traffic between services, and from services to data stores, is encrypted in transit.

## Secrets

- No secrets in code, config, specs or infra definitions.
- At startup the service fetches its secrets from the approved secret store.
- Administrative and debug endpoints must not be reachable from the public internet.
- Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.

## Logging

- Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.

## App and ops

- External input is validated against a schema; invalid requests are rejected.
- Inbound and outbound webhooks include an HMAC signature and a timestamp; verification of both is mandatory on the receiving side.
- Error responses carry no stack traces, SQL or internal hostnames.
- Queries are parameterized; no string concatenation of user input.
- CI scans dependencies and images; critical vulns fixed within 14 days.
- Service-to-service calls are authenticated, either with mutual TLS between the workloads or with a signed workload identity token.
- Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.
- Containers keep the default root user, because switching to a non-root user broke access to the mounted files.

## Notes on behavior

Transfers are two-phase: reserve on the source wallet, credit the target, then confirm; a crash between phases is resolved by the saga on restart. A top-up is accepted as pending and flips to completed when the funding source confirms. Profile changes take effect immediately and are echoed in the response.

# Reference material for the wallet

## Wallet model in detail

A wallet belongs to one customer and has one currency. A customer can have one wallet per currency. The wallet holds a balance, which is the sum of all booked transactions, and an available balance, which is the balance minus the amounts of pending top-ups that are not yet confirmed and of transfers that are being booked.

| Field | Meaning | Example |
|---|---|---|
| id | identifier of the wallet | wal_5521 |
| owner_name | name of the wallet owner | Alma Berg |
| balance | booked balance in minor units | 12850 |
| currency | ISO 4217 code | EUR |
| status | active or closed | active |
| created_at | creation time in UTC | 2025-11-02T10:14:00Z |

### Transaction types

| Type | Direction | Created by |
|---|---|---|
| topup | in | a confirmed top-up from a funding source |
| transfer_out | out | a transfer to another wallet |
| transfer_in | in | a transfer from another wallet |
| fee | out | a fee of a product, for example a faster payout |
| correction | in or out | the operations team, with a reason |

Every transaction carries an id, the type, the amount, the currency, the time of booking and a reference text of at most 140 characters. Transactions are never changed after booking. A mistake is corrected by a new transaction of the type `correction`.

## Top-ups

A top-up moves money from a funding source of the customer to the wallet. The customer chooses the funding source in the app. The request arrives with the amount and the identifier of the funding source. The service creates a transaction in the status `pending` and asks the funding provider to collect the money. When the provider confirms, the transaction becomes `booked` and the available balance increases. When the provider refuses, the transaction becomes `failed` and nothing changes in the balance.

The limits of a top-up depend on the level of the wallet.

| Wallet level | Minimum | Maximum per top-up | Maximum per month |
|---|---|---|---|
| basic | 5.00 EUR | 500.00 EUR | 2,000.00 EUR |
| standard | 5.00 EUR | 2,500.00 EUR | 10,000.00 EUR |
| premium | 5.00 EUR | 10,000.00 EUR | 40,000.00 EUR |

A top-up that would break a limit is refused with the answer `limit_exceeded` and the name of the limit.

## Transfers

A transfer moves money from one wallet to another wallet in the same currency. The sender chooses the receiver by phone number or by the name of the receiver, and the app resolves the choice to a wallet id before it sends the request. The note of the transfer is shown to both sides.

Rules of a transfer:

1. Both wallets must be `active`.
2. The amount must be at least 0.01 and at most the available balance of the sender.
3. The currencies of both wallets must be equal.
4. The sender and the receiver must be different wallets.
5. Both balances change in one database transaction.

Failures have their own answers: `wallet_closed`, `insufficient_funds`, `currency_mismatch` and `same_wallet`.

### Examples

A customer with 40.00 EUR sends 15.50 EUR to a friend. After the transfer the sender has 24.50 EUR and the friend has 15.50 EUR more. Both see a transaction with the note, the sender as `transfer_out` and the friend as `transfer_in`.

A customer with 10.00 EUR tries to send 12.00 EUR. The service answers `insufficient_funds` and the app shows the missing amount of 2.00 EUR with a button that opens the top-up screen.

## Profile data

The profile holds the name of the owner, the phone number and the address. A change of the name is visible in new transfers immediately; old transactions keep the name that was valid at the time. The phone number must be in international format and unique among the wallets, because it is the way friends find each other. The address has the fields street, number, postal code, city and country.

## The mobile app screens

The app has five screens that use the service.

- **Home** shows the balance, the last five transactions and the buttons for top-up and send.
- **Top-up** shows the funding sources and the amount field with the limit of the wallet level.
- **Send** shows the contact search, the amount, the note field and a summary before the customer confirms.
- **History** shows all transactions in pages of 50, newest first, with a filter for the type.
- **Profile** shows the owner data and lets the customer change the name, the phone number and the address.

## Capacity

The wallet serves 1.8 million customers at the start and is dimensioned for 4 million in two years. On a normal day the service books 90 thousand transactions, on the last day of the month up to 350 thousand.

| Operation | Median | 95th percentile |
|---|---|---|
| read wallet | 15 ms | 40 ms |
| list transactions (page of 50) | 38 ms | 95 ms |
| transfer | 85 ms | 210 ms |
| top-up request | 120 ms | 300 ms |
| profile change | 30 ms | 80 ms |

## Reconciliation job

Every night at 02:00 UTC the reconciliation job computes, for every wallet, the sum of its transactions and compares it with the stored balance. Differences are written into a table that the finance team reads in the morning. In the first month of the pilot, 3 of 1.8 million wallets showed a difference; all were caused by a manual correction that had been entered twice and was reversed.

## Release plan

| App release | Wallet service change | Share of customers |
|---|---|---|
| 4.1 | read endpoints | 100 percent |
| 4.2 | top-ups and transfers | 10 percent, then 100 percent |
| 4.3 | profile changes | 100 percent |
| 4.4 | transaction filters | 100 percent |

## Glossary

- **Available balance**: balance minus pending amounts.
- **Funding source**: a bank account or a card from which a customer tops up.
- **Minor unit**: the smallest unit of the currency, for example the cent.
- **Reference**: free text that a customer adds to a transfer.
- **Correction**: a booking by the operations team that fixes an earlier booking.

## Questions of the app teams

**Why is my balance different from the available balance?** Pending top-ups and transfers in progress are not counted in the available balance.

**Can a closed wallet receive money?** No; a transfer to a closed wallet is refused with `wallet_closed`.

**Are transactions sorted by booking time?** Yes, newest first; transactions with the same time are sorted by id.

**How long does a top-up take?** Usually a few seconds; some funding sources need up to two working days and the transaction stays `pending` meanwhile.

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
