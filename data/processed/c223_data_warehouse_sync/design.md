# Data Warehouse Sync (formerly "Reporting Feed" and "Analytics Export")

## Background

The Data Warehouse Sync copies tables from the analytics read replica to a staging bucket, where the analytics vendor picks the extracts up for the warehouse. The job replaces the Analytics Export of the monolith (the "export cron" in older diagrams) and the Reporting Feed of the old data platform. In this document the new job is called sync-job; older material calls it "the feed" or "the exporter".

## Goals

- Provide the analytics team with fresh extracts of the tables they need every night.
- Make the list of copied tables a configuration, not code, so that a new table does not need a release.
- Report for every run how many rows were copied per table.

## Components

- **sync-job** is the scheduled job. It runs every night at 02:00 UTC and takes about forty minutes.
- **analytics read replica (PostgreSQL)** is the read-only copy of the production database from which sync-job reads. It lags the production database by a few seconds.
- **staging bucket (S3)** receives the extract files. Each run writes into a folder named after the date.
- **Analytics vendor** picks the files up from the staging bucket for the warehouse. The vendor is called "the BI partner" in the older documents.

## How a run works

sync-job reads the list of tables from its configuration. For each table, it reads the rows changed since the last successful run, writes them into files of at most one million rows and uploads the files into the folder of the day. When all tables are done, sync-job writes a manifest file with the table names, the file names and the row counts. The vendor starts its load only when the manifest exists.

If a table fails, sync-job continues with the next table and marks the run as `partial`. The manifest then lists the failed tables, and the analytics team gets a message in their channel. The next run repeats the failed tables from their last successful position.

## Configuration

Each table entry has a name, the key column, the column that tells which rows changed, and an optional list of columns to leave out. A change of the configuration takes effect with the next run.

## Recovery

The analytics read replica and the production database it copies have point-in-time recovery enabled, with seven days of retention. A failed run can be repeated by hand for a chosen date with the same configuration; the files of the day are replaced.

Security incidents of this service follow a runbook with a named on-call owner, and the team rehearses an incident twice a year.

## Capacity

The extracts of the largest table have about forty million rows. The job needs about two gigabytes of memory and finishes within the time window of one hour; if the data volume grows by fifty percent, the window has to be extended or the largest table split into two jobs.

## Rollout

The old Analytics Export keeps running for two weeks after the first successful run of sync-job. During this time the vendor compares the files of both. When the comparison shows no differences for ten nights in a row, the old export is switched off.

## Open items

- Naming of the folders: date only, or date and run number (see the section on reruns in the Reporting Feed document).
- Whether the vendor needs a second manifest for the tables that are copied weekly instead of nightly.
