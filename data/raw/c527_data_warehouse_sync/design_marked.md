# warehouse sync - design meeting notes

People: data platform, finance analytics, platform team. Goal: decide how the nightly copy for the analytics vendor works.

## What it is

Nightly job (sync-job, sometimes called "the exporter") copies selected tables from the analytics read replica into the staging bucket (S3). The analytics vendor downloads the extract files from the bucket. Only for the finance reports. Columns: customer id, country, amount, currency, payment date.

## Decisions

- Job starts at 01:00, table by table, one file per table and date, big tables split in parts of one million rows.
- ⟦F2|The analytics read replica (PostgreSQL) is created from the production database, and the team will look at the settings of the cloud account later.⟧
- ⟦S:CHG-01|A second engineer reviews each production change before it is deployed.⟧
- Replicas and backups: ⟦S:RES-02|backups and replicas of the personal data of customers in the EU stay in regions of the EU as well⟧.
- Debugging: ⟦F1|traces record the full request including the name and the email of the customer, because that is the default of the tracing agent and nobody wants to maintain a filter⟧. Concern from the platform team, left as it is for now.

⟦S:PRV-03|Each use of customer data is tied to a purpose in the privacy notice shown at sign-up, and a new purpose needs a new notice and new consent.⟧
- ⟦S:CHG-02|Every change to production has a rollback plan that has been tested in a pre-production environment.⟧
- ⟦S:PIP-01|Credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour.⟧

## Reversed

- First: the job runs at 03:00. Then the vendor said they need the files at 06:00 at the latest, so 01:00.
- First: one big file per table. Dropped, files are split above five million rows (TBD whether one million is the best size).

## Failure

If the replica is not reachable the job tries again three times, five minutes apart, and stops with `failed`. The finance team gets an e-mail when the last extract is older than 36 hours.

## Open questions

- How the vendor confirms that a file was processed (TBD).
- Whether the job also runs on the first day of the month a second time (TBD).

## Next

Data platform writes the job, finance analytics gives the list of tables, platform team sets up the pipeline.
