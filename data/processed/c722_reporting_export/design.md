reporting export - ticket collection

RPT-1 what it does
export-job writes the scheduled reports to the exports bucket (S3), reads from the reporting read replica (PostgreSQL), runs in the reporting private subnet.

RPT-2 jobs
The export-job runs under a service account whose password engineers use to log in when they debug.

RPT-3 support cases
The weekly export of support cases contains the full card numbers.

RPT-4 other
- Balances are reconciled with the ledger every day and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.
- Differences found in a reconciliation are resolved within 5 working days.
- A replaced version of the report format is kept 12 months, removal announced 90 days ahead.
- The merchant sandbox has generated data only and runs separately from production.
- Unprocessable messages go to the dead-letter queue, examined within one working day.
