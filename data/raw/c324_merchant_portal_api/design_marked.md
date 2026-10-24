# Merchant Portal API: stories and design

Epic: PORTAL-200 (Merchant portal, reporting and users)
Status: In development

## Overview

This epic delivers settlements, user management and transaction reports for merchants. The request path is Merchant web app, Portal Gateway, portal-backend and portal-db (PostgreSQL). The gateway validates tokens against Keycloak before forwarding requests to portal-backend.

## Stories

### PORTAL-201: Settlements

As a finance user, I want to list settlements and open one so that I can reconcile payouts.

Acceptance criteria:
- GET /v1/settlements returns my merchant's settlements and can be filtered by status.
- GET /v1/settlements/{settlementId} returns id, period, gross, fees and net.

### PORTAL-202: Users

As a merchant owner, I want to invite colleagues and change their roles.

Acceptance criteria:
- POST /v1/users accepts email and role and returns id, email and role.
- PATCH /v1/users/{userId}/role accepts the new role and returns the user.
- An account always keeps at least one owner.

### PORTAL-203: Reports

As a finance user, I want to request a transaction report and download it.

Acceptance criteria:
- POST /v1/reports accepts report_type, from_date and to_date and returns a job with id, status and expires_at.
- GET /v1/reports/{reportId}/download returns the finished report until it expires.

## Delivery notes

1. All traffic is served over HTTPS only.
2. Requests are validated against strict schemas.
3. Audit trail: ⟦F1|audit logs follow the default log retention of about a month and are not write-protected.⟧ Finance accepted this for the first release.

## Non-functional requirements

| Area | Requirement |
|---|---|
| Authentication | ⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧ |
| Authorization | ⟦S:AUTHZ-01|Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.⟧ |
| Admin surface | ⟦S:AUTHZ-04|Admin and debug endpoints are reachable only from the internal network, not from the public internet.⟧ |
| Access review | ⟦S:AUTHZ-05|Every three months the system owners review who has access to production and remove what is no longer needed.⟧ |
| Encryption at rest | ⟦S:CRYPTO-01|All personally identifiable information is encrypted before it lands on disk, using AES-256.⟧ |
| Algorithms | ⟦S:CRYPTO-05|The approved algorithm list is followed, and MD5, SHA-1, DES, 3DES and ECB mode are prohibited in this service.⟧ |
| Secrets in artifacts | ⟦S:SECRET-01|Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.⟧ |
| Network | ⟦S:NET-01|portal-db and the message brokers sit in private subnets and are not publicly reachable.⟧ |
| Security logging | ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧ |
| Minimization | ⟦S:DATA-01|The portal collects and stores only the personal data needed to run merchant accounts.⟧ |
| Third parties | ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧ |
| Exports | ⟦S:DATA-05|Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.⟧ |
| Queries | ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧ |

⟦S:CRYPTO-03|All public-facing endpoints terminate TLS 1.2 or higher.⟧
⟦S:API-01|Schema validation runs on every external input, and invalid data never reaches the business logic.⟧
⟦S:LOG-04|Access to centralized logs must be limited to authorized staff.⟧

## Design notes

Reports are produced by a background worker that reads from a replica. A job moves through requested, running and ready, and failed jobs carry a reason and can be requested again. Large date ranges are processed in chunks that are merged when all chunks finish. The download endpoint streams the file so memory use on the service stays flat. Settlement figures come from a table filled nightly by the finance pipeline; the portal never writes to it.

## Definition of done

- All acceptance criteria demonstrated in staging.
- OpenAPI file updated and published.
- Dashboard for report queue length and failure rate exists.

# Reference material for the merchant portal

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
