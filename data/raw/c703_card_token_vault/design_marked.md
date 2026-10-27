# Card Token Vault: Architecture Description

## 1. Components

The card token vault consists of the tokenization-service, the vault-db (PostgreSQL), Vault and KMS, and the vault private subnet.

## 2. Operations

The vault offers tokenize, detokenize, delete and lookup. The lookup operation returns a masked number and the expiry date.

## 3. Commitments

3.1 Reconciliation. ⟦S:REC-01|The balances are reconciled with the ledger every day, and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.⟧ ⟦F3|Reconciliation differences are discussed and closed in the finance channel, no ticket is created.⟧

3.2 Idempotency. ⟦S:IDM-01|Every operation that moves money takes an idempotency key, and a repeated request with the same key does not move the money again.⟧

3.3 Limits. ⟦S:LIM-01|The daily outgoing transfers of a customer are limited by the limit table, and a change of a limit needs the approval of a second employee.⟧

3.4 Interfaces. ⟦S:VER-01|A replaced API version is kept for 12 months, and its removal is announced 90 days in advance.⟧ ⟦F1|Fields are renamed in place when it makes the API cleaner, and customers are told in the chat.⟧

3.5 Messaging. ⟦S:MSG-01|Messages that cannot be processed go to a dead-letter queue, which is examined within one working day.⟧


3.7 Support. ⟦F2|Card numbers are masked on the search page, the detail page shows the full number.⟧
