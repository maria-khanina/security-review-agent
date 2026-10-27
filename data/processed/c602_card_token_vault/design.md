# Card Token Vault

## Overview

The card token vault exchanges primary account numbers for tokens. Other services store and send the token only. When a service needs the real number, for example to talk to the acquirer, it asks the vault.

```
caller -> tokenization-service -> vault-db
                 |
              Vault / KMS
```

## Components

- **tokenization-service**: the only entrance to the vault
- **vault-db** (PostgreSQL): tokens and the stored numbers
- **Vault and KMS**: key storage
- **vault private subnet**: the network the components live in

## Operations

| Operation | Input | Output |
|---|---|---|
| tokenize | account number, expiry | token |
| detokenize | token | account number, expiry |
| delete | token | confirmation |
| lookup | token | masked number, expiry, created_at |

## Behavior

Tokenizing the same number twice gives the same token for the same merchant and different tokens for different merchants. Tokens are 24 characters. A token that was deleted can not be used again. Lookup never returns the full number.

## Failure modes

- vault-db not reachable: tokenize and detokenize answer `unavailable`, the caller retries with backoff
- key service slow: calls wait up to 3 seconds, then `unavailable`

## Events

Every token event (created, used, deleted) is also sent to our fraud partner Riskly for scoring; the register entry of the vault lists only internal consumers.

## Operating the vault

- The owner and the deputy of the vault are named in the service register.
- Test accounts in production are removed within 7 days after the test ends.
- High alerts are acknowledged within 15 minutes.
- Payments above 10,000 EUR are held for review by the fraud team before they are settled.
- Transaction records are kept for 7 years and deleted within 90 days after.

## Rollout

Staged by caller: gateway first, then wallet, refund and merchant portal. Each caller migrates its stored numbers with a one-time job.

## Open

- batch tokenize for the migration jobs?
- token length 24 or 32?
