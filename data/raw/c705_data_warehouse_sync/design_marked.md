Data Warehouse Sync

```
sync-job --> analytics read replica (PostgreSQL)
   |
   +--> staging bucket (S3) <-- Analytics vendor
```

How to read it: the sync-job reads the replica every night and writes files to the staging bucket, which the analytics vendor reads.

Reconciliation
- ⟦F2|Reconciliation differences are tracked in the finance chat and not in a ticket.⟧

API versions
- ⟦S:VER-01|A replaced version of the API is kept for 12 months and its removal is announced 90 days in advance.⟧
- ⟦S:VER-02|Breaking changes are released only as a new version of the API.⟧

Queues
- ⟦F1|A message that fails three times is dropped.⟧
- ⟦F3|The retention of the queue is set to the maximum of the provider, 14 days, whether the messages were processed or not.⟧

Jobs
- ⟦S:JOB-01|Every scheduled job has its own service account, and the account cannot log in interactively.⟧

Support
