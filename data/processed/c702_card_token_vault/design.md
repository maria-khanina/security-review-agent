# Card Token Vault - Design and Commitments (v1.0, roadmap-aligned)

Our vision: the fastest and safest tokenization in the company!

## What it is

The vault exchanges card numbers for tokens. The tokenization-service is the only entrance, vault-db (PostgreSQL) stores the numbers, Vault and KMS keep the keys, and everything lives in the vault private subnet.

## Delivery highlights

- tokenize, detokenize, delete and lookup of a token
- p99 below 50 ms
- Only the payment endpoint of the vault clients is idempotent; for transfers the caller has to make sure that it does not send twice.

## Quality

- Differences found in a reconciliation are resolved within 5 working days.
- A replaced API version is kept for 12 months, and its removal is announced 90 days in advance.
- Breaking changes are released only as a new version of the API.
- Each scheduled job runs with its own service account, which cannot log in interactively.
- Support agents see card numbers and document numbers only in masked form.

## Merchant testing

Merchants can test with real card numbers in the sandbox, which makes their integration tests realistic.

## Events

Processed messages of the token events are archived in a bucket and nothing is ever deleted from it, so that we can replay them.
