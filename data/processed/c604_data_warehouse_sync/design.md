# Data Warehouse Sync: Design

## Background and goals

The analytics team reads selected production tables every morning. The sync job copies them each night so that analysts do not query the production database. An analytics vendor reads the copy in a staging bucket and builds the dashboards for the business.

Aims of this design: a stable nightly copy, a staging area that the vendor can read, and no load on production during the day.

## Non-goals

- real-time sync, the business is happy with one day of delay
- transformations, the vendor does them

## What it consists of

The sync-job is a scheduled service. It reads from an analytics read replica (PostgreSQL) and writes files to a staging bucket (S3). The Analytics vendor reads the files from the staging bucket. The sync-job is a small container that runs on the shared batch cluster.

## Tables in scope

customers, accounts, transactions, refunds, merchants, support_cases. Each table is written as one file per night, in parquet format, with the date in the file name.

## Behavior of the job

At 01:00 the job starts, reads the tables in a fixed order and writes the files. A table that fails is retried twice and then skipped, and the vendor sees the old file with the old date. At 04:00 a small check job compares row counts between replica and files and posts the result to the data channel.

## Records

Transaction records stay in the replica and the staging bucket, nobody has set up their deletion because the vendor may need the history for its models. Documents uploaded by customers are deleted within 30 days after the account is closed, in the replica as well as in the staging bucket.

## Exports and tests

Exported files that contain personal data are encrypted, and they are deleted from the download location after 7 days. Exports of more than 1,000 customer records need the written approval of the data owner. Production data is not copied to test or development environments, the job is tested with a generated data set.

## Operating the service

The register lists the personal data that the sync job processes and the analytics vendor as the third party that receives data from it. The components of the job are never more than two major versions behind the latest release, and the register shows their versions. Alerts of severity high are acknowledged within 15 minutes.

## Rollout plan

The first copy runs for two weeks next to the old manual exports. After that the manual exports stop.

## Open questions

- one file per table per night or partitions?
- who owns the check job?
