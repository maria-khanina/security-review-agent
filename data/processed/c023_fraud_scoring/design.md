# Fraud scoring v2: migration delta

This note lists only what changes relative to the nightly batch scorer ("rules batch", sometimes called fraud-batch in older tickets). Anything not listed here behaves as before. The old design document is no longer maintained.

## What changes

1. **From nightly to real time.** The batch job scored the previous day's payments in one run. The new scoring-engine consumes payment events from payment-events (MSK) as they happen and writes a decision for each payment within seconds.
2. **Storage.** Decisions move from a table in the shared reporting database to a dedicated PostgreSQL database, decisions-db. The old table remains available as a fallback during cutover.
3. **Infrastructure as code.** The batch scorer was configured by hand. The new stack is fully declared in Terraform: a KMS key (`scoring_key`), the MSK cluster (`payment_events`), the RDS instance (`decisions_db`), a security group (`decisions_sg`), a log group (`scoring_audit`) and an IAM policy (`scoring_policy`).
4. **Audit.** Every decision writes an audit record to the log group `scoring_audit`; the batch job only wrote a summary line per run.

## What stays the same

The rule set, the thresholds and the decision labels (allow, review, block) are unchanged. The model score is still produced by the same library, and analysts still receive the review queue by email in the morning.

## Data

The engine reads these fields from each event: payment id, amount, country, device id, customer email and phone, and the history counters. It writes decision, score and reasons. Customer attributes are kept next to the decision so analysts can see what was scored.

decisions-db (PostgreSQL) stores every decision together with the customer attributes that were scored, and it is the only datastore the engine writes to.

No personal data is sent to third parties; any future transfer would be made only under an approved data processing agreement and with just the fields required.

## Reporting

The old reporting queries are replaced by one parameterized search over decisions. For the analyst search by merchant and date range, the service appends the raw SQL fragment from the query string to the report query, so analysts can add their own conditions. The same endpoint exports the filtered list to CSV for the analysts.

## Security changes

Most properties are inherited from the batch scorer and are not repeated here. These are the points that changed shape with the new stack:

- Data at rest is encrypted with KMS-managed keys.
- The database accepts connections only from the application subnet.
- The approved algorithm list is followed, and MD5, SHA-1, DES, 3DES and ECB mode are prohibited in this service.
- Traffic between services and to data stores must be encrypted in transit.
- Source, config, specs and infrastructure definitions contain no secrets.
- Workloads are non-root, and read-only root filesystems are used wherever they can be.
- At startup the service fetches its secrets from the approved secret store.
- Each service must use its own database account with the minimum grants and no shared administrative credentials.
- Only the HTTP access logs from the load balancer are kept for the scoring-engine.
- Logs contain no secrets, card numbers or personal data beyond opaque identifiers.
- Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less.

## Cutover plan

Week one runs the new engine in shadow mode: it scores every event but its decisions are not used. Week two compares shadow decisions with the batch decisions for the previous day and reports the disagreement rate. If the rate is below the agreed threshold, week three switches the review queue to the new decisions. The batch job is switched off one week later. The old reporting table is retired once the cutover is confirmed (an older runbook still lists four scoring replicas; two is correct).

## Open items

- Alert thresholds for consumer lag on payment-events.
- Whether the analyst CSV export needs a row limit.
