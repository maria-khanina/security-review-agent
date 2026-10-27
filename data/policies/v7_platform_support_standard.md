# Meridian Pay Platform Operations and Support Standard

This standard sets the controls for the movement of money, the interfaces offered to merchants, queues and scheduled jobs, and the work of the support agents. Each requirement is numbered so that audit findings can cite it. Where a requirement says "must", deviation needs an approved exception.

# Section POS-1: Movement of Money

POS-1.1 Balances must be reconciled with the ledger every day, and a difference of more than 0.01 EUR must be reported to the finance team within 24 hours. POS-1.2 Differences found in a reconciliation should be resolved in a timely manner. POS-1.3 Operations that move money must be idempotent: a repeated request with the same key must not move the money again. POS-1.4 The daily outgoing transfers of a customer must be limited to the amount in the limit table, and a change of a limit needs the approval of a second employee.

# Section POS-2: Interfaces

POS-2.1 A replaced version of an API must be kept for 12 months, and its removal must be announced 90 days in advance. POS-2.2 Breaking changes of an API should be released only as a new version of the API. POS-2.3 The sandbox for merchants must contain no real customer data and must run separately from production.

# Section POS-3: Queues and Jobs

POS-3.1 Messages that cannot be processed must be moved to a dead-letter queue and be examined within one working day. POS-3.2 Messages in queues must be deleted after they are processed. POS-3.3 Messages may be kept for up to 7 days to allow a replay. POS-3.4 Scheduled jobs must run with their own service account that cannot log in interactively.

# Section POS-4: Support

POS-4.1 Support agents must see card numbers and document numbers only in masked form. POS-4.2 Changes to the contact data of a customer require adequate verification.
