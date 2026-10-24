# Fraud Scoring Service: Design and Compliance Statement

Document owner: Risk Compliance
Version: 1.1 (reviewed by Security Architecture)

## 1. Purpose and Scope

This document describes the design of the Fraud Scoring Service ("the Service") and records, for each applicable requirement of the Meridian Pay Information Security Policy, the control by which the Service satisfies that requirement. It applies to the production environment and to the environments that support it. The Service evaluates every payment event in near real time and writes a decision of allow, review or block.

## 2. Functional Description

The Service consists of the following components:

- payment-events (MSK), the input topic carrying one event per payment together with customer attributes;
- scoring-engine, the service that reads each event, applies rules and a model, and produces a decision;
- decisions-db (PostgreSQL), the datastore for decisions and the customer attributes that were scored;
- the scoring audit log group, which receives an audit record for each decision.

The infrastructure is declared in Terraform. It consists of the KMS key `scoring_key`, the MSK cluster `payment_events`, the database instance `decisions_db`, the security group `decisions_sg`, the log group `scoring_audit` and the IAM policy `scoring_policy`.

### 2.1 Processing

For each event the scoring-engine first applies deterministic rules, for example rules that detect a device used in several countries within a short period. If a rule yields a block decision, the decision is final. Otherwise the engine computes a model score between zero and one and maps it to allow, review or block using configured thresholds. The reasons for the decision are a short list of the rules or features that influenced it, and they are stored together with the decision.

### 2.2 Review handling

Decisions of type review are collected into a queue that is delivered to the fraud analysts every morning. Analysts record their conclusion, and the conclusion is stored alongside the original decision. The conclusion does not alter the stored model score. This separation allows the model to be evaluated against analyst conclusions over time.

## 3. Controls

3.1 In accordance with policy,

3.2 ⟦S:CRYPTO-01|Personally identifiable information held in decisions-db is encrypted at rest with AES-256.⟧

3.3 ⟦S:CRYPTO-05|Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.⟧

3.4 ⟦S:SECRET-01|No secrets are kept in source code, config files, API specs or infrastructure definitions.⟧

3.5 ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store when the Service starts.⟧

3.7 ⟦S:LOG-01|The audit trail includes authentication failures, privilege changes and sensitive-data access.⟧

3.8 ⟦S:LOG-02|Log lines are kept free of secrets, card numbers and personal details, and identifiers are opaque.⟧

⟦S:AUTH-02|Calls between our own services carry a signed workload identity token or use mutual TLS, and the receiving service checks it.⟧

3.9 ⟦S:DATA-02|Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.⟧

3.10 ⟦S:DATA-03|Third parties receive only the fields they need, and only if an approved data processing agreement covers them.⟧

3.11 ⟦S:API-05|All queries use bound parameters instead of string concatenation.⟧

⟦S:AUTHZ-04|Nothing administrative or meant for debugging can be called from outside our network.⟧

3.12 ⟦S:OPS-01|The continuous integration pipeline scans dependencies and container images, and critical vulnerabilities are fixed within 14 days.⟧

## 4. Operational Characteristics

The Service is stateless: all counters used by the rules are carried in the payment event, so several instances of the scoring-engine may run concurrently and Kafka divides the events between them. The number of partitions of the input topic caps the degree of parallelism; the initial setting is sufficient for the expected volume and may be raised before seasonal peaks. Consumer lag is monitored, and an alert fires when the lag exceeds a threshold that is defined in the operations runbook.

Model updates are deployed separately from the engine. A new model version first runs in shadow mode, where it scores every event but its decisions are recorded without effect. Its decisions are compared with those of the active model for a defined period, and the new version is promoted only if the disagreement rate is within the agreed bounds. Rollback to the previous model version is a configuration change and takes effect for new events immediately.

## 5. Outstanding Items

- Alert threshold for consumer lag: value TBD with Operations.
- Final naming of the review queue mailbox: TBD with the fraud analyst team.

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

# Appendix 1: related system, Merchant Portal API; reference material for the merchant portal

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
