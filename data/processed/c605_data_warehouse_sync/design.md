Data Warehouse Sync - design doc (v2, ESL)

Purpose
This service make copy of production tables to staging bucket every night, so analytic vendor can read it and not touch production database.

Parts
1. sync-job (service) - run every night 01:00
2. analytics read replica (PostgreSQL) - the job read from it
3. staging bucket (S3) - the job write files here
4. Analytics vendor - read from bucket

How it work
The job read six tables: customers, accounts, transactions, refunds, merchants, support_cases. One parquet file for each table. If a table fail, the job try again two times, then it skip table and the vendor see old file.

Analyst work
Analysts export tables from the replica with the sync tool for their own analyses and tell the data owner afterwards.

Rules we follow
- Transaction records are kept for 7 years and deleted in 90 days after the 7 years end.
- Documents uploaded by customers are deleted within 30 days after the account is closed.
- Vulnerability rated critical is fixed in production within 7 days after it is published.
- Components are not more than two major versions behind the latest release, and the service register show the version of each.
- Test account in production is removed within 7 days after the test ends.
- Exported file with personal data is encrypted and deleted from the download location after 7 days.
- Owner and deputy of the service are named in the service register.
- The service register list the personal data of the sync job and the third party that receive the data, the analytics vendor.

Open
- partition the files by month?
- time of the job, 01:00 or 02:00?
