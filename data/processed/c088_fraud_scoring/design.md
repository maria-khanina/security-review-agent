# Fraud scoring v2: migration delta

This note describes only what changes relative to the nightly batch scorer (fraud-batch in the old tickets). Anything not mentioned here behaves as before. Reference: the old design in the archived wiki space (link may not open).

## What changes

1. **Real time.** The batch job scored the previous day's payments in one run. The new scoring-engine consumes payment events from payment-events (MSK) as they happen and writes a decision within seconds.
2. **Storage.** Decisions move from a table in the shared reporting database to a dedicated PostgreSQL database, decisions-db. The old table stays available as a fallback during cutover.
3. **Infrastructure as code.** The batch scorer was configured by hand. The new stack is declared in Terraform: a KMS key (`scoring_key`), the MSK cluster (`payment_events`), the RDS instance (`decisions_db`), a security group (`decisions_sg`), a log group (`scoring_audit`) and an IAM policy (`scoring_policy`).
4. **Enrichment.** The engine now enriches each event with signals from an external device-intelligence vendor before scoring. The scoring-engine calls the vendor once per event and uses the answer as one of the model features.
5. **Audit.** Every decision writes an audit record to the log group `scoring_audit`; the batch job only wrote a summary line per run.

## What stays the same

The rule set, the thresholds and the decision labels (allow, review, block) are unchanged. The model score still comes from the same library, and analysts still receive the review queue by email in the morning.

## Data

The engine reads from each event the payment id, amount, country, device id, customer email and phone, and the history counters. It writes a decision, a score and reasons. decisions-db (PostgreSQL) holds the decisions together with the customer attributes that were scored, and the scoring-engine and the analyst tooling both read from it.

Personal data has a defined retention period and is deleted when it expires or on a verified request from the data subject. The retention value for review decisions is not final.

## Deployment

The scoring-engine runs as two replicas that share one Kafka consumer group, and it starts with the usual platform bootstrap. Rolling updates replace one replica at a time. An older runbook lists four replicas; two is correct.

## Security changes

Most properties are inherited from the batch scorer and are not repeated. The points below changed shape with the new stack:

- The database sits in private subnets with no public endpoint.
- Personal data is encrypted at rest with AES-256.
- Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- Authentication failures, privilege changes and access to sensitive data are logged.
- Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids.
- All queries use bound parameters instead of string concatenation.
- Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less.

## Cutover plan

Week one runs the new engine in shadow mode: it scores every event, but its decisions are not used. Week two compares shadow decisions with the batch decisions for the previous day and reports the disagreement rate. If the rate is below the agreed threshold, week three switches the review queue to the new decisions. The batch job is switched off one week later, and the old reporting table is retired once the cutover is confirmed.

## Open items

- Alert thresholds for consumer lag on payment-events.
- Whether the analyst CSV export needs a row limit.
