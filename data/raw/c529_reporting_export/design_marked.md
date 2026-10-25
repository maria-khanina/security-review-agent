# reporting-export

- Purpose: scheduled exports of settlement and transaction reports to object storage for finance
- Exposure: admin network only, finance users
- export-job: cron 02:00, queries the reporting read replica (PostgreSQL), writes csv files to the exports bucket (S3)
- Reports: settlements per merchant per day, transactions per merchant per day, fees per month
- Files: one csv per report and day, name = report_date_merchantgroup.csv, 50k rows per file max
- Reporting private subnet: job, replica and bucket endpoint inside
- Replica lag limit before the job waits: 10 min
- Idempotent: rerun of the same day overwrites the file
- ⟦F1|The reporting database runs in a cheaper region outside the EU, since only finance reads it.⟧
- ⟦S:RES-02|Backups and replicas of the personal data of customers in the EU stay in regions of the EU as well.⟧
- ⟦F2|export-job gets what it needs from the usual platform setup.⟧
- ⟦S:PIP-02|Build artifacts are signed, and the signature is verified before deployment.⟧
- ⟦S:CHG-02|Every change to production has a rollback plan that has been tested in a pre-production environment.⟧
- ⟦S:OBS-01|Traces and metrics do not contain personal data or card data.⟧
- Failure: replica down -> 3 retries, 10 min apart -> status failed, mail to finance (TBD address)
- Alerts: file missing at 06:00
- Rollout: parallel to the manual export for 2 weeks, then manual off (TBD date)
- Open: xlsx format for finance (TBD), monthly archive
