# Data Warehouse Sync - Design

## 1. Goal

Every night the Data Warehouse Sync copy the selected tables of the production database to a staging bucket. The analytics vendor read the files from the bucket and use them for the reports of the finance team. The sync is made for the finance reports only and it is not a general data platform.

## 2. Components

- **sync-job** is a program that start every night at 01:00, reads the tables and write the files.
- **analytics read replica (PostgreSQL)** is the copy of the production database from which sync-job read. In this way the production database has no load from the extract.
- **staging bucket (S3)** keeps the extract files until the vendor take them.
- **Analytics vendor** is the external company that process the files.

## 3. Flow

sync-job reads the tables from the analytics read replica and write the extract files to the staging bucket. The vendor download the files from the bucket. The extract contain the columns that the finance team need: customer id, country, the amount, the currency and the date of the payment. The list of the tables is kept in a configuration file of the job.

## 4. Behaviour of the job

The job do the extract table by table. For every table it write one file with the name of the table and the date. When the table is bigger than five million rows, the file is split in parts of one million rows. If one table fail, the job go on with the next table and report the failure in the end. The vendor get a message when all files are ready.

## 5. Data location

Personal data of customers in the EU is stored and processed only in regions of the EU. The replica and the staging bucket are in the same region as the production database.

## 6. Customer requests

When a customer asks to delete the data, the team of the production database delete the customer record. The sync does not touch the extract files that already exist, so the copies of the customer in the reports and in the exports stay where they are.

A second engineer reviews each production change before it is deployed.

## 7. Backups

The replica and the bucket have backups every week. To save money, the backups are copied to a bucket in a region outside the EU, where the storage is cheaper.

## 8. Delivery

The job is deliver by the pipeline of the platform team. Credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour. sync-job is packed in a container image by the pipeline and the image is started on the schedule of the cluster.

Every service exposes a health endpoint that the shared dashboard polls every minute, and the error rate of each endpoint is shown on the dashboard.

## 9. Change

Every change to production has a rollback plan that has been tested in a pre-production environment. A change of the list of the tables is a change to production too.

## 10. Observability

The dashboards show the duration of the job, the number of rows per table and the age of the last successful extract.

## 11. Failure modes

When the replica is not reachable, the job try again three times with a pause of five minutes and then stop with the status `failed`. When the bucket is full or not reachable the job do the same. The finance team get an e-mail when the last extract is older than 36 hours.

## 12. Rollout

First the job run in parallel to the old manual export for two weeks, and the finance team compare the numbers. After this the manual export is stopped.

## 13. Open questions

- How the vendor confirm that a file was processed.
- If the job should run on the first day of the month a second time.
