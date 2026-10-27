ledger service. brain dump. will clean up later

the ledger is the book of all money movements. double entry. every entry is balanced, nobody edits, only reversals. wallet and payments post to it. parts: ledger-core (the service), ledger-db (postgres), ledger-events (kafka) where every posted entry is published.

endpoints: POST /v1/entries, GET /v1/entries/{entryId}, GET /v1/accounts/{accountId}/balance, POST /v1/entries/{entryId}/reversal, GET /v1/entries

what we promise (compliance made me write it all down):
and ⟦S:REC-02|differences found in a reconciliation are resolved within 5 working days⟧.

money operations: ⟦F2|idempotency keys are remembered for one minute.⟧

limits: ⟦F1|limits are set in the code and changed only by a release.⟧


queues: ⟦S:MSG-01|messages that cannot be processed go to a dead-letter queue, which is examined within one working day⟧, ⟦S:MSG-02|messages are deleted from the queue after they are processed⟧.

jobs: ⟦S:JOB-01|every scheduled job runs with its own service account, which cannot log in interactively⟧.

support: ⟦S:SUP-01|support agents see card numbers and document numbers only in masked form⟧.

todo: pagination
