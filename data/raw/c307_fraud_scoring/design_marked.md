# Fraud Scoring Service - Design Document

Author: Pawel S., Risk Engineering
Status: For review

## 1. Introduction

The Fraud Scoring Service evaluate every payment in the near real time and write a decision: allow, review or block. It replace the nightly batch job. The service read the payment events from the MSK topic, apply the rules and the model, and store the result.

## 2. Components

- **payment-events (MSK)** - input topic, one event for every payment with the customer attributes.
- **scoring-engine** - the service which read the events, calculate the score and write the decision.
- **decisions-db (PostgreSQL)** - store the risk decisions.
- **scoring audit log group** - the place in CloudWatch where audit records are written.

The infrastructure is created with Terraform. There are six resources: the KMS key `scoring_key`, the MSK cluster `payment_events`, the database `decisions_db`, the security group `decisions_sg`, the log group `scoring_audit` and the IAM policy `scoring_policy`.

## 3. Data flow

First, payment-events send the payment event to the scoring-engine. Second, the scoring-engine write the risk decision to decisions-db. Third, the scoring-engine write an audit record to the scoring audit log group. There is no other data flow.

## 4. Access control

⟦S:AUTH-02|Calls to the scoring-engine from the other internal services are authenticated with mutual TLS or signed workload identity tokens.⟧ ⟦S:AUTH-03|The access tokens expire in 15 minutes at maximum, and the refresh tokens are rotated on every use.⟧

## 5. Data protection

⟦S:CRYPTO-01|Personal data in our databases and object storage is encrypted at rest with AES-256, using keys held in the corporate key management service.⟧ ⟦S:CRYPTO-06|The encryption keys are held in KMS, never stored with the data which they protect, and rotated at least annually.⟧

⟦S:DATA-05|Reports and exports with personal data are available only to authorized users, stored encrypted, and deleted after 7 days.⟧

⟦S:CRYPTO-04|The traffic between services, and between services and data stores or brokers, is encrypted in transit.⟧ ⟦S:CRYPTO-07|The services validate the TLS certificates and never disable the verification.⟧ ⟦S:CRYPTO-05|We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.⟧

⟦S:LOG-04|Only authorized staff can access the central logs.⟧

⟦S:LOG-02|We scrub logs so that they contain neither secrets, card numbers nor personal data other than opaque identifiers.⟧

 ⟦S:DATA-03|The personal data is sent to third parties only under an approved data processing agreement, and only the fields which are required.⟧

## 6. Secrets

⟦S:SECRET-01|No secrets are kept in source code, config files, API specs or infrastructure definitions.⟧ ⟦S:SECRET-02|The runtime secrets are fetched from the approved secret store when the service start.⟧

⟦S:DATA-02|We keep personal data for 12 months at most and delete it automatically when the period ends, or earlier on a verified request.⟧

## 7. Network

⟦S:NET-01|The database and the message brokers are in the private subnets and are not publicly reachable.⟧ ⟦F4|Outbound firewall rules are managed by each team and are rarely reviewed.⟧

⟦S:AUTHZ-03|Database credentials are per service with least-privilege grants, and no shared admin account is used by the application.⟧

## 8. Callbacks

When the decision is block, the service call back the payments team and also receive the callbacks from the partner sandbox during the integration tests. ⟦F3|The signature verification is skipped for the callbacks from the partner sandbox.⟧ The reason is that the sandbox of the partner is not able to sign the messages yet.

## 9. Logging

⟦S:LOG-01|The audit trail includes authentication failures, privilege changes and sensitive-data access.⟧

## 10. Application and operations

⟦S:API-05|User input reaches the database only as query parameters, never as part of the query text.⟧ ⟦S:OPS-01|The CI scan the dependencies and images, and the critical vulnerabilities are fixed within 14 days.⟧ ⟦S:OPS-02|No container runs as root, and the root filesystem is read-only wherever possible.⟧

⟦S:AUTHZ-04|Nothing administrative or meant for debugging can be called from outside our network.⟧

## 11. Storage and testing

⟦F1|The decisions-db (PostgreSQL) is the only datastore which the engine writes to, and it runs as a primary with a standby in the second availability zone.⟧ The engine is tested in the test environment with the usual functional tests. ⟦F2|The scoring-engine is exercised in the test environment by the functional test suite.⟧

## 12. How the decision is made

The engine first apply the simple rules, for example the same device used in three countries in one hour. If a rule say block, the decision is made without the model. Otherwise the model give a score between 0 and 1 and the thresholds map it to allow, review or block. The reasons, a short list of the rules or features which influenced the score, are stored with the decision so the analysts can understand it.

The engine is stateless. All the counters come from the payment event itself, so we can run several copies of the engine, and Kafka divide the events between them.

## 13. Open points

- The alert thresholds for the consumer lag are not decided.
- The name of the mailbox for the review queue.

# Reference material for fraud scoring

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
