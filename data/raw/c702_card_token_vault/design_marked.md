# Card Token Vault - Design and Commitments (v1.0, roadmap-aligned)

Our vision: the fastest and safest tokenization in the company!

## What it is

The vault exchanges card numbers for tokens. The tokenization-service is the only entrance, vault-db (PostgreSQL) stores the numbers, Vault and KMS keep the keys, and everything lives in the vault private subnet.

## Delivery highlights

- tokenize, detokenize, delete and lookup of a token
- p99 below 50 ms
- ⟦F3|Only the payment endpoint of the vault clients is idempotent; for transfers the caller has to make sure that it does not send twice.⟧

## Quality

- ⟦S:REC-02|Differences found in a reconciliation are resolved within 5 working days.⟧
- ⟦S:VER-01|A replaced API version is kept for 12 months, and its removal is announced 90 days in advance.⟧
- ⟦S:VER-02|Breaking changes are released only as a new version of the API.⟧
- ⟦S:JOB-01|Each scheduled job runs with its own service account, which cannot log in interactively.⟧
- ⟦S:SUP-01|Support agents see card numbers and document numbers only in masked form.⟧

## Merchant testing

⟦F2|Merchants can test with real card numbers in the sandbox, which makes their integration tests realistic.⟧

## Events

⟦F1|Processed messages of the token events are archived in a bucket and nothing is ever deleted from it, so that we can replay them.⟧
