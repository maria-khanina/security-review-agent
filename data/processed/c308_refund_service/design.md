# Refund Service: Turning Refunds into a Customer Experience Advantage

## The opportunity

A refund is the moment of truth in a payment relationship. Merchants who refund quickly and transparently keep their customers; merchants who do not, lose them. The Refund Service gives Meridian Pay merchants a single, reliable place to return money, and gives our support teams the tools to help when a merchant cannot. This is a platform capability: one engine, many channels, zero friction.

## The solution at a glance

At the heart of the solution is **refund-core**, the decision engine that checks a request against the original payment, applies the approval rules and orchestrates the return of the money. In front of it sits **Refunds Gateway**, the single entry point for merchant integrations and for the support console. Behind it sit **refund-db (PostgreSQL)**, the trusted record of every refund, and **refund-events (Kafka)**, the real-time stream that keeps the ledger and the notifications in step.

## Value pillars

**Speed.** Small refunds are approved on the spot and the customer sees the money back within the card network's normal time.

**Transparency.** Every refund has a status that merchants can query at any time: pending, approved, completed, failed or cancelled. Merchants can filter their refunds by status or by payment.

**Control.** Larger refunds are routed to a second approver, so that merchants keep control over the money that leaves their balance.

## The developer experience

Five operations cover the whole lifecycle: create a refund, read one, list many, approve or reject, and cancel a pending one. Creating a refund takes a payment reference, an amount, a currency and a reason. The response returns the refund with its identifier and status. Refunds Gateway is the single entry point to the service and routes each request to refund-core.

## Security by design

We believe security is an enabler of growth, and we have built it into the foundation of the product.

The API enforces per-client rate limits.

Every request to an externally reachable endpoint is authenticated, either with an OIDC bearer token or with a mutual TLS client certificate. Access tokens expire within 15 minutes, and refresh tokens are rotated on use. Unlimited login attempts are allowed, for convenience.

Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.

Calls between our own services carry a signed workload identity token or use mutual TLS, and the receiving service checks it.

Nothing administrative or meant for debugging can be called from outside our network. Every employee who has access to the service gets the admin role, to avoid waiting for permission tickets.

At rest, personal data is protected with AES-256 in both the database and object storage, with keys from the corporate key management service. Primary account numbers never reach our storage in clear text, because the card token vault tokenizes them first. Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not. Keys are managed in KMS, never stored next to the encrypted data, and rotated annually. TLS certificate verification is enabled in all clients, with no option to disable it.

Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.

No secrets are kept in source code, config files, API specs or infrastructure definitions. At startup the service fetches its secrets from the approved secret store.

External APIs must sit behind a WAF with rate limiting.

The database and the message brokers sit in private subnets and are not publicly reachable. Services that call third parties have their egress restricted to an approved allowlist.

We log failed logins, changes of privileges and reads of sensitive data. Third parties receive only the fields they need, and only if an approved data processing agreement covers them. Test and staging environments use synthetic data, never real personal data or card data.

Reading centralized logs requires authorization, and only approved staff have it.

Schema validation runs on every external input, and invalid data never reaches the business logic. Every webhook we send or receive is signed with an HMAC, and the receiver checks the signature together with the timestamp. The API returns sanitized errors with no stack traces, SQL fragments or internal hostnames. Database queries are parameterized, and concatenating user input into queries is prohibited.

Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks. Workloads are non-root, and read-only root filesystems are used wherever they can be.

Rate limit per client: 60 requests per minute, with HTTP 429 and a Retry-After header once the limit is hit.

Traffic between services, and from services to data stores, is encrypted in transit.

## Roadmap

Next quarter we extend the engine to partial refunds with several instalments, add a merchant dashboard for refund analytics and explore instant refunds to wallets. Success is measured by the share of refunds completed within one hour, merchant satisfaction and the reduction in refund-related support contacts. See the earlier concept note "Returns 2.0" for the market sizing (link no longer available).

# Reference material for refunds

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
