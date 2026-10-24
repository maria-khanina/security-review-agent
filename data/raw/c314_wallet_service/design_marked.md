# Wallet Service Design (with explanations for new team members)

Author: Kenji, Wallet team (first big design doc, comments welcome!)

## 1. What is this service?

A wallet is like a digital piggy bank. Each customer has one wallet per currency, and the wallet holds a balance. The Wallet Service is the backend that knows how much money is in each wallet, lets customers top up from a funding source such as a bank account, and lets them send money to other wallets. The mobile app is the only client. It never talks to the database directly, which is a very important rule in every backend: clients talk to services, services talk to databases.

## 2. The building blocks

I will explain each box, because I found it hard to understand them when I joined.

- **Mobile API Gateway.** This is the front door. Every request from the mobile app goes through it first. Think of it like the reception desk of an office building: it checks who you are before letting you go upstairs.
- **Keycloak.** This is the identity provider (IdP). It knows our customers and it can say "yes, this token is valid" or "no, it is not". The gateway asks Keycloak every time.
- **wallet-core.** This is the brain. It contains the business rules: can this wallet send this amount, what happens if two transfers arrive at the same time, and so on.
- **wallet-db (PostgreSQL).** This is the memory. It stores balances, the list of transactions and the profile of the owner.

The path of a request is: Mobile app, then gateway, then Keycloak for validation, then back to the gateway, then wallet-core, then wallet-db. The answer travels back the same way.

## 3. The API

Here are the five calls, with their fields, so you know what the mobile app sends and receives.

- GET /v1/wallets/{walletId} returns the wallet: id, owner_name, balance and currency.
- POST /v1/wallets/{walletId}/topups adds money from a funding source. The app sends amount and funding_source_id. The reply is a transaction with id, type, amount and created_at.
- POST /v1/transfers moves money between wallets. The app sends from_wallet_id, to_wallet_id, amount and a free-text note. The reply has the same transaction shape.
- GET /v1/wallets/{walletId}/transactions lists the transactions of one wallet, newest first.
- PATCH /v1/wallets/{walletId}/profile changes owner_name, phone_number or address and returns the wallet.

Card numbers are never returned by the API. When a customer adds a card as funding source, the app only ever sees the funding_source_id afterwards.

## 4. Who are you? Authentication explained

Authentication means proving who you are. In our system the proof is a token, a small signed piece of text that the app gets after login and attaches to each request. A token is not the same as a password: the password is used once, the token is used for every call, and that is why it must expire quickly.

⟦S:AUTH-01|Public endpoints reject any call that carries neither a valid OAuth2 bearer token nor a client certificate.⟧ ⟦S:AUTH-03|A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use.⟧ Rotating means that every time the app uses a refresh token to get a new access token, it also gets a new refresh token and the old one stops working. That way a stolen refresh token has a very short life.

⟦S:AUTH-05|Passwords are stored only as salted argon2id hashes.⟧ A hash is a one-way fingerprint of the password: you can check a password against it, but you cannot get the password back. The salt is a random value added before hashing so two customers with the same password get different hashes.

⟦S:AUTH-06|The login and token endpoints throttle repeated failures and apply a temporary lockout once an account reaches ten consecutive failed attempts.⟧ This stops someone from trying thousands of passwords.

⟦S:LOG-04|Access to the centralized logging system is restricted to authorized people.⟧

## 5. Authorization: what are you allowed to do?

Authorization is different from authentication. Even a valid customer must only see their own wallet. ⟦S:AUTHZ-01|For every request on a customer-owned resource, the service verifies that the caller owns the resource or is entitled to it.⟧ Example: if customer A asks for the transactions of wallet B, wallet-core answers with an error, not with the data.

 ⟦S:AUTHZ-04|Debug and administrative routes are not exposed to the internet.⟧

## 6. Protecting the data

⟦S:CRYPTO-01|At rest, personal data is protected with AES-256 in both the database and object storage, with keys from the corporate key management service.⟧ "At rest" means while it sits on disk, as opposed to "in transit", while it travels over the network. ⟦S:CRYPTO-06|Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.⟧ ⟦S:CRYPTO-05|We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.⟧ ⟦S:CRYPTO-07|Services validate the certificates of the servers they call, and verification is never turned off.⟧

 ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧ ⟦F3|Load tests run against a restored production backup, so the test environment holds real customer data.⟧

For the partner's analytics we needed a quick solution. ⟦F1|The database has a public endpoint so the partner's reporting tool can read from it.⟧ We agreed that this is the fastest way to get them started.

## 7. Secrets

⟦S:SECRET-01|No secrets are kept in source code, config files, API specs or infrastructure definitions.⟧ ⟦S:SECRET-02|The approved secret manager is the only source of runtime secrets, fetched at start-up.⟧

## 8. Edge protection and network

⟦S:NET-05|Requests from the internet reach the API only through the WAF, where rate limits are enforced.⟧ ⟦S:NET-04|Outbound calls to third parties are restricted to an approved allowlist.⟧

⟦S:CRYPTO-04|Traffic between services, and from services to data stores, is encrypted in transit.⟧

## 9. Input handling

⟦S:API-01|All external input is validated against a schema, and invalid requests are rejected.⟧ ⟦S:API-04|Clients get generic error messages without stack traces, SQL or internal hostnames.⟧ ⟦S:API-05|All queries use bound parameters instead of string concatenation.⟧ ⟦S:API-03|Webhook payloads, inbound and outbound, carry an HMAC signature and a timestamp, and the receiver verifies both.⟧ A signature is like the wax seal on a medieval letter: it proves who sent the message and that nobody changed it.

⟦S:API-02|A single API client may send at most 1000 requests per hour, and the 1001st request gets HTTP 429.⟧

⟦S:DATA-02|Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.⟧

## 10. Logs

Logs are the diary of the system. ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are written to the logs.⟧ When something fails in production, debugging is much easier with a lot of detail, so ⟦F2|stack traces with customer data are written to the shared log index.⟧

## 11. Build and run

⟦S:OPS-01|Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less.⟧ ⟦S:OPS-02|The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only.⟧

⟦S:DATA-05|Download links for reports with personal data work for 24 hours, and the files are encrypted in storage and deleted after 7 days.⟧

⟦S:AUTH-02|Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.⟧

## 12. What happens during a transfer?

A transfer has two steps. First wallet-core reserves the amount on the source wallet, so the money cannot be spent twice. Second it credits the target wallet and confirms the reservation. If the service crashes between the steps, a recovery job finishes or cancels the transfer when the service starts again. The transfer reference makes the call idempotent: sending the same reference twice returns the first transaction instead of moving money twice.

A top-up starts as pending. When the funding source confirms the payment, the status changes to completed and the balance grows. If the funding source rejects it, the status becomes failed and the balance stays as it was.

## 13. Open questions

- What is the maximum amount of a single transfer? Product has not decided.
- Should the profile change require a confirmation code? Needs a talk with the UX team.

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

# Appendix 1: related system, Fraud Scoring; reference material for fraud scoring

## Input of a score

The scoring-engine reads one event per payment from the payment-events topic. Each event carries the fields below.

| Field | Meaning | Example |
|---|---|---|
| payment_id | identifier of the payment | pay_0042c9 |
| amount | amount in minor units | 8000 |
| currency | ISO 4217 code | EUR |
| country | country of the card issuer | DE |
| device_id | identifier of the device | dev_88a1 |
| merchant_category | merchant category code | 5411 |
| hour | local hour of the payment | 23 |
| history counters | number of payments of the customer in the last hour, day and week | 1, 4, 19 |

The engine adds derived features: the ratio between the amount and the average amount of the customer, whether the country differs from the country of the previous payment, and whether the device is new for the customer.

## Output of a score

The engine writes one decision per payment.

| Field | Meaning | Example |
|---|---|---|
| payment_id | the scored payment | pay_0042c9 |
| score | number between 0 and 1 | 0.37 |
| decision | allow, review or block | allow |
| reasons | the three features that influenced the score most | amount_ratio, new_device, night_hour |
| model_version | the model that produced the score | m-2026-03 |
| scored_at | time of the decision, UTC | 2026-03-14T23:02:41Z |

### Thresholds

| Score | Decision |
|---|---|
| below 0.60 | allow |
| 0.60 to 0.85 | review |
| above 0.85 | block |

If one of the fixed rules matches, the decision is made without the model. The rules are: a payment above 5,000 EUR from a new device is sent to review; more than ten payments of the same customer within one minute are blocked.

## The review queue

Payments with the decision `review` go to the queue of the analysts. An analyst sees the payment, the reasons and the history of the customer, and decides to confirm the payment or to block it. The outcome is stored with the decision and is used to train the next model.

| Week | Payments scored | Reviewed | Confirmed fraud |
|---|---|---|---|
| shadow week 1 | 1,150,000 | 21,800 | 1,240 |
| shadow week 2 | 1,180,000 | 22,400 | 1,310 |
| shadow week 3 | 1,210,000 | 20,900 | 1,190 |
| shadow week 4 | 1,260,000 | 21,100 | 1,260 |

## Model updates

The model is trained on the stored decisions, with the analyst outcomes as labels. A new model is compared with the current one on the same events for one week in shadow mode. It goes live when it finds at least as much confirmed fraud at the same share of reviews.

| Model | Reviews per 1,000 payments | Fraud found per 1,000 reviews |
|---|---|---|
| m-2026-01 | 19.3 | 58 |
| m-2026-02 | 18.8 | 60 |
| m-2026-03 | 17.9 | 62 |

## Capacity

The engine scores about 1.3 million payments per day on average, with peaks of 55 payments per second. It is dimensioned for 200 payments per second.

| Measure | Median | 95th percentile |
|---|---|---|
| time from event to decision | 46 ms | 120 ms |
| consumer lag of the topic | 0.2 s | 1.4 s |
| decisions written per second at peak | 55 | 78 |

## Operation of the consumer group

The two copies of the engine share one consumer group. The topic has twelve partitions, so each copy reads six. When a copy stops, the other takes over its partitions after the rebalance, which takes about thirty seconds. The lag grows during the rebalance and falls again within two minutes.

## Roadmap

| Quarter | Content |
|---|---|
| 1 | card payments |
| 2 | wallet transfers |
| 3 | refunds |
| 4 | device and account links |

## Glossary

- **Score**: the number that expresses how risky a payment looks.
- **Decision**: allow, review or block.
- **Shadow mode**: a new model scores events without its decisions being used.
- **Consumer group**: the set of readers that share the partitions of a topic.
- **Lag**: the number of events that wait to be read.

## Questions of the risk team

**Can the thresholds change without a new model?** Yes, they are configuration.

**How is the history of a customer kept?** The counters are updated by the engine with each event.

**What happens to a payment while it waits in the queue?** It is already decided; `review` means the payment is let through and checked afterwards.

**Why do some reasons repeat?** The same few features are the strongest for most payments.

# Appendix 2: related system, Merchant Portal API; reference material for the merchant portal

## Settlement model

A settlement is the payout to a merchant for a period. The finance pipeline creates settlements; the portal only reads them.

| Field | Meaning | Example |
|---|---|---|
| id | identifier of the settlement | stl_2026_03_0418 |
| period | the days the settlement covers | 2026-03-01 to 2026-03-07 |
| gross | sum of captured payments in minor units | 4821900 |
| fees | fees taken by Meridian Pay in minor units | 62700 |
| net | gross minus fees | 4759200 |
| currency | ISO 4217 code | EUR |
| status | open, closed, paid | paid |

### Settlement periods

Merchants choose a settlement period when they sign up: daily, weekly or monthly. The period ends at midnight UTC. A settlement is `open` while the period runs, `closed` after the finance pipeline has computed it, and `paid` after the payout has left the bank.

| Period | Closing | Payout |
|---|---|---|
| daily | next morning | two working days after closing |
| weekly | Monday morning | two working days after closing |
| monthly | first working day | three working days after closing |

## Reports

Merchants request reports of three types.

| Report type | Content | Typical size |
|---|---|---|
| transactions | one row per payment in the range | 20 thousand rows |
| settlements | one row per settlement in the range | 60 rows |
| fees | fees by type and day | 400 rows |

A report covers at most thirteen months. Reports are created in the background; the portal shows `pending` until the file is ready. The file is a CSV with a header line. Amounts in the file are written with a decimal point and two decimals, and dates use the format `YYYY-MM-DD`. Merchants can ask for the semicolon as the separator.

### Scheduled reports

A merchant can schedule a report to run every week or every month. The scheduled report uses a moving date range: "last month" always means the previous calendar month. The result appears in the list of reports and an email with a link is sent to the person who scheduled it.

## Team area

A merchant account has a list of people who use the portal. The team area lists them with the email address and a status: `invited`, `active` or `removed`. A new person is added by sending an invitation to an email address; the status is `invited` until the person has accepted. People who leave the merchant are marked `removed` and disappear from the default view, but stay in the list when the filter "all" is chosen.

## The web app

The Merchant web app has four areas: the dashboard with the last settlements and a chart of volume per day, the settlements list, the reports area and the team area. The dashboard chart shows the last 30 days and the same days of the previous month for comparison.

### Filters of the settlements list

| Filter | Values |
|---|---|
| status | open, closed, paid |
| period | a date range |
| currency | the currencies of the account |

## Capacity

The portal has about 38 thousand merchant accounts at the start. On a normal working day 6,500 merchants log in; on Mondays, when weekly settlements close, up to 14,000.

| Operation | Median | 95th percentile |
|---|---|---|
| list settlements (page of 20) | 55 ms | 140 ms |
| read a settlement | 20 ms | 50 ms |
| send an invitation | 90 ms | 210 ms |
| request a report | 60 ms | 130 ms |
| generate a transactions report (20 thousand rows) | 14 s | 31 s |

## Release plan

| Release | Content | Merchants |
|---|---|---|
| 1 | settlements and users | pilot group of ten |
| 2 | reports | pilot group, then 25 percent |
| 3 | scheduled reports | 25 percent, then all |
| 4 | dashboard chart | all |

## Glossary

- **Gross**: the sum of all captured payments in the period.
- **Net**: gross minus fees.
- **Settlement**: the payout for a period.
- **Report**: a file with the data of a period.
- **Invitation**: the email that adds a person to the team area.

## Questions of merchants

**Why does my settlement not include yesterday's payments?** Settlements are computed after the period closes; yesterday's payments are in the open settlement.

**Can I change the settlement period?** Yes, through support; the change applies from the next period.

**Why is a report still pending?** Large reports take a few minutes; the status changes to ready when the file is complete.

**How many people can the team area list?** Fifty.
