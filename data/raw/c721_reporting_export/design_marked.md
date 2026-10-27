# Reporting Export - Design Document

## 1. Purpose

Scheduled settlement and transaction reports for finance. The export-job reads the reporting read replica (PostgreSQL) and writes files to the exports bucket (S3). The reporting private subnet isolates the components.

## 2. Schedule

Settlements daily at 05:00, transactions weekly on Monday at 06:00, month end on the 1st.

## 3. Commitments


3.2 ⟦S:REC-02|Differences found in a reconciliation are resolved within 5 working days.⟧

3.3 ⟦S:VER-01|A replaced version of the report format is kept for 12 months, and its removal is announced 90 days in advance.⟧


3.5 ⟦S:SBX-01|The merchant sandbox contains only generated data and runs separately from production.⟧



3.8 ⟦S:JOB-01|Every scheduled job runs with its own service account, which cannot log in interactively.⟧

3.9 ⟦S:SUP-01|Support agents see card numbers and document numbers only in masked form.⟧
