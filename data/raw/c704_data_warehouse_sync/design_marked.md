Data warehouse sync - how it works (ticket collection)

DWS-1 nightly copy
sync-job reads six tables from the analytics read replica (PostgreSQL) and writes parquet files to the staging bucket (S3). The analytics vendor reads the files.

DWS-2 failures
Table fails -> retried twice -> skipped, vendor sees old file. Check job at 04:00 compares row counts.

DWS-3 reconciliation
⟦F2|The daily reconciliation reports only differences above 100 EUR to finance.⟧

DWS-4 interfaces
The vendor reads files, the files have a version in the name. ⟦F1|Old file layouts stay as long as somebody complains about their removal.⟧ ⟦S:VER-02|Breaking changes of the file layout are released only as a new version.⟧

DWS-5 queue
sync events go through a small queue: ⟦S:MSG-01|messages that cannot be processed go to a dead-letter queue which is examined within one working day⟧; ⟦S:MSG-02|processed messages are deleted from the queue⟧.

DWS-6 job accounts

DWS-7 support
