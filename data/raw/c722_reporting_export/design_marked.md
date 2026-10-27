reporting export - ticket collection

RPT-1 what it does
export-job writes the scheduled reports to the exports bucket (S3), reads from the reporting read replica (PostgreSQL), runs in the reporting private subnet.

RPT-2 jobs
⟦F1|The export-job runs under a service account whose password engineers use to log in when they debug.⟧

RPT-3 support cases
⟦F2|The weekly export of support cases contains the full card numbers.⟧

RPT-4 other
- ⟦S:REC-01|Balances are reconciled with the ledger every day and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.⟧
- ⟦S:REC-02|Differences found in a reconciliation are resolved within 5 working days.⟧
- ⟦S:VER-01|A replaced version of the report format is kept 12 months, removal announced 90 days ahead.⟧
- ⟦S:SBX-01|The merchant sandbox has generated data only and runs separately from production.⟧
- ⟦S:MSG-01|Unprocessable messages go to the dead-letter queue, examined within one working day.⟧
