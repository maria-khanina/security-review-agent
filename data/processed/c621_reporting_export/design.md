Reporting export - copy from the slack thread

**what**: export-job writes the scheduled settlement and transaction reports to the exports bucket (S3) for finance. reads from the reporting read replica (PostgreSQL). everything inside the reporting private subnet.

**schedule**: settlement report daily 05:00, transactions weekly Monday 06:00, month-end report on the 1st.

**format**: csv + a checksum file per report

**retries**: if the replica is behind by more than 10 min the job waits and tries again every 5 min until 08:00, then pages.

**what finance asked for**
- Exported files that contain personal data are encrypted and deleted from the download location after 7 days.
- Exports of more than 1,000 customer records need the written approval of the data owner.

**what compliance asked for**
- Critical vulnerabilities are fixed in production within 7 days after publication.
- Components are not more than two major versions behind the latest release, register shows versions.
- Messages to customers have no card numbers, passwords or images of identity documents.
- Owner and deputy named in the service register.
- The register lists the personal data of the export job and each third party that receives data from it.
- High alerts are acknowledged within 15 minutes.

**todo** xlsx instead of csv?
