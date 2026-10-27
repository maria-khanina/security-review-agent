# Reporting Export: Value Proposition and Design

Finance is our most important customer, and this service gives them what they need: reliable, scheduled reports with no manual work.

## What it does

The export-job runs on a schedule, reads the reporting read replica (PostgreSQL) and writes settlement and transaction reports to the exports bucket (S3). Everything runs in the reporting private subnet. Finance picks the files up from the bucket.

## Reports

| Report | When | Content |
|---|---|---|
| settlements | daily | all settlements of the previous day |
| transactions | weekly | all transactions of the previous week |
| month end | 1st of the month | totals per merchant |

## Quality

- Critical vulnerabilities are fixed in production within 7 days after publication.
- Components are never more than two major versions behind the latest release and the register shows each version.
- The service register names an owner and a deputy.
- The register lists the personal data of the export job and every third party that receives data from it.
- Alerts of severity high are acknowledged within 15 minutes.

## Files

Report files stay in the exports bucket until someone cleans it up, which we do when finance asks us.

## Customers

When a customer closes the account, the uploaded documents are deleted when the customer requests it; nothing happens automatically.

## Support

Support replies to finance questions quote the card number that the customer wrote in the ticket, so that nothing gets lost.

## Next

Self-service for finance: pick the period and download.
