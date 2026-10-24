# KYC Verification Service: Architecture and Security Control Catalogue

Author: Rina M., Security Champion, Identity Team
Review: Security Architecture
Revision: 5 (rev 4 used the name "KYC-Gateway" for kyc-orchestrator; the old name is retired but still appears in two dashboards)

## 1. Summary

The KYC Verification Service collects identity details and identity document images from customers, submits them to an external identity verification vendor, and keeps the outcome of each verification case. It is one of the most sensitive services in the platform because it holds government identity documents, so its controls are catalogued here in detail. Reviewers should read the catalogue (section 5) first and the architecture afterwards.

## 2. Architecture

The customer application calls kyc-orchestrator. kyc-orchestrator stores document images in the kyc-documents bucket (S3) and case records in kyc-db (PostgreSQL), and sends verification requests to the Identity verification vendor. The vendor returns its result through a signed callback.

There are five operations:

- POST /v1/kyc/cases opens a case (customer_id, full_name, date_of_birth, country) and returns id, status, risk_level and customer_id.
- POST /v1/kyc/cases/{caseId}/documents uploads a document (document_type, content_base64) and returns document_id and received_at.
- GET /v1/kyc/cases/{caseId} returns the case status.
- POST /v1/kyc/cases/{caseId}/submit submits the case to the vendor; the request carries the customer's consent flag.
- GET /v1/kyc/cases lists cases.

## 3. Case lifecycle

A case moves from opened to documents_received to submitted, and then to verified, rejected or manual_review. Manual review is handled by the operations team, who may ask the customer for more documents. A new submission after a rejection opens a new case. The risk level is assigned by the vendor and stored unchanged.

## 4. Customer sign-in

Customers sign in through the corporate identity provider, and the customer application presents the resulting token to the service. kyc-orchestrator relies on the corporate identity provider for the sign-in of customers and does not keep any credentials of its own. Session handling in the mobile and web clients is described in the client design and is out of scope here.

kyc-orchestrator serves case and document requests on behalf of the signed-in customer, and it returns the case and document data that the request refers to.

## 5. Control catalogue

The catalogue follows the Information Security Policy. Identifiers (K-1 and so on) match the compliance spreadsheet (link TBD; the older spreadsheet is stale).

### 5.1 Identity and access

- K-1: No external endpoint serves anonymous traffic; callers present an OAuth2 token or a TLS client certificate.
- K-2: A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use.
- K-4: Administrative and debug endpoints are not reachable from the public internet.

### 5.2 Data protection

- K-5: Encryption at rest with AES-256 covers personal data in databases and object storage, and its keys live in the corporate key management service.
- K-6: Key material is kept in KMS and separate from the data, and keys are rotated every year or sooner.
- K-7: Personal data is never placed in URLs.
- K-8: Card numbers are never returned by the API.
- K-9: Third parties receive only the fields they need, and only if an approved data processing agreement covers them.

Traffic between services and to data stores must be encrypted in transit.
- K-10: Non-production environments contain no real personal or card data.
- K-11: Customer deletion requests: deletion requests are handled manually and often forgotten. A tracking dashboard is on the roadmap.

### 5.3 Cryptography and transport

- K-13: Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.
- K-14: Services validate the certificates of the servers they call, and verification is never turned off.

### 5.4 Secrets

- K-15: Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.

Access to centralized logs must be limited to authorized staff.
The API enforces a limit of 300 requests per minute for each client and answers HTTP 429 when it is exceeded.
- K-16: Runtime secrets are fetched from the approved secret store at startup.

Logs carry opaque identifiers only and never include secrets, card numbers or personal data.

### 5.5 Network

- K-18: kyc-db and the message brokers sit in private subnets and are not publicly reachable.
- K-19: The kyc-documents bucket blocks public access and is private by default.
- K-20: Third-party calls leave through an egress allowlist, not through open outbound access.

### 5.6 Logging

- K-21: The audit trail includes authentication failures, privilege changes and sensitive-data access.

### 5.7 Application security

- K-23: All external inputs are validated against a schema and rejected if invalid.
- K-25: Signature verification is skipped for the callbacks coming from the partner sandbox.
- K-26: Internal details such as stack traces, SQL and hostnames never appear in an error response.
- K-27: User input reaches the database only as query parameters, never as part of the query text.

### 5.8 Operations

- K-28: CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days.
- K-29: Containers run as a non-root user, with a read-only root filesystem where possible.

The external API sits behind a WAF that also applies rate limiting.

## 6. Document handling details

Uploaded images are limited in size and checked for type before they are accepted. Each document is stored under a random object key that does not contain customer identifiers. The service never renders documents for the customer after upload; only the operations team can view them during manual review. Documents belonging to a rejected case remain linked to the case so that a later dispute can be handled with the original evidence.

## 7. Open items

- Status column for the catalogue: the controls above are listed without an implementation status; the spreadsheet carries the status (link TBD).
- The vendor callback retry window is unconfirmed.
- Reference to the previous KYC design (v1) is in the archived wiki space and may not open.

# Reference material for the verification flow

## Case model

A verification case follows one customer through the identity check. A customer can have several cases over time, for example after a change of name, but only one case can be open at once.

| Field | Meaning | Example |
|---|---|---|
| id | identifier of the case | case_7710 |
| customer_id | the customer the case belongs to | cus_30481 |
| status | open, submitted, approved, rejected, needs_review | submitted |
| risk_level | unknown, low, medium, high | low |
| created_at | time the case was opened, UTC | 2026-02-03T08:40:12Z |
| updated_at | time of the last change, UTC | 2026-02-03T08:47:55Z |

### Status changes

| From | To | Trigger |
|---|---|---|
| open | submitted | the customer gives consent and the case is sent to the vendor |
| submitted | approved | the vendor reports a match with low or medium risk |
| submitted | rejected | the vendor reports a mismatch |
| submitted | needs_review | the vendor does not answer in five minutes, or reports an unclear result |
| needs_review | approved | an analyst accepts the case |
| needs_review | rejected | an analyst rejects the case |

A case in `approved` or `rejected` is closed. A new check needs a new case.

## What the customer enters

The customer enters the full name, the date of birth and the country of residence, and photographs one identity document. The supported documents depend on the country.

| Country group | Accepted documents |
|---|---|
| EU and EEA | passport, national identity card, driving licence |
| United Kingdom | passport, driving licence |
| Other | passport only |

For documents with two sides, such as identity cards, the customer photographs both sides, and the app uploads them as two documents of the same case. The app helps with the photograph: it shows an outline, checks the sharpness and the brightness, and asks for a new picture if the text cannot be read.

## The vendor exchange

When a case is submitted, the orchestrator sends the vendor the data of the customer and the references of the images. The vendor answers asynchronously through a callback. The callback carries the vendor request id, the result (`match`, `mismatch`, `unclear`) and a risk level suggested by the vendor.

The orchestrator maps the result to a status. A `match` with the risk level `low` or `medium` becomes `approved`; a `match` with the risk level `high` becomes `needs_review`; a `mismatch` becomes `rejected`; an `unclear` result becomes `needs_review`. The vendor sends each answer at most once, but the orchestrator ignores a second answer for the same request id.

## The review queue

Cases in `needs_review` appear in the queue of the analysts. The queue is sorted by age, oldest first. An analyst opens a case, sees the data of the customer and the images, and decides to accept or reject. The decision needs a short comment. The target is that no case waits longer than four working hours.

| Week | Cases in review (average) | Share of all cases |
|---|---|---|
| pilot week 1 | 41 | 7.8 percent |
| pilot week 2 | 36 | 6.4 percent |
| pilot week 3 | 29 | 5.1 percent |
| pilot week 4 | 27 | 4.7 percent |

The share fell because the app now rejects pictures that are too dark before the upload, which removed many unclear results.

## Capacity

The service handles about 2,400 new cases per day at the start and is dimensioned for 10,000. A case produces on average 2.3 images of about 1.4 MB each.

| Operation | Median | 95th percentile |
|---|---|---|
| open a case | 70 ms | 160 ms |
| upload an image | 380 ms | 900 ms |
| read a case | 25 ms | 60 ms |
| submit | 150 ms | 340 ms |
| list cases (page of 20) | 45 ms | 110 ms |

The vendor needs 40 seconds at the median and 3 minutes at the 95th percentile to answer.

## Localization

The app is available in eleven languages. The error messages of the service are codes, and the app translates them. The names of countries use the ISO 3166 two-letter codes; the app shows the local names. Dates of birth are sent as `YYYY-MM-DD` and shown in the format of the phone.

## Release plan

| App release | Service change |
|---|---|
| 5.0 | read endpoints and case status screen |
| 5.1 | opening cases and uploading documents, ten percent of new customers |
| 5.2 | all new customers |
| 5.3 | customers with an existing case in the old platform |

## Glossary

- **Case**: one run of the identity check for one customer.
- **Vendor**: the external company that compares the document and the data.
- **Analyst**: a member of the operations team who reviews cases.
- **Risk level**: the estimate of the vendor how likely the identity is false.
- **Needs review**: a case that a person has to decide.

## Questions of the app team

**Can the customer change the name after the case is submitted?** No. The case has to be rejected or finished first.

**How many pictures can a case have?** Up to six.

**What does the app show for `needs_review`?** A neutral message that the check takes longer than usual.

**Can the customer start a second case while one is open?** No, the service answers `case_already_open`.

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
