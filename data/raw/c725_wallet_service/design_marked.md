# Wallet Service: Product-Driven Design

We are building the wallet that customers love!

## Parts

Mobile API Gateway (entrance), wallet-core (service), wallet-db (PostgreSQL), Keycloak (identity provider).

## API

GET /v1/wallets/{walletId}, POST /v1/wallets/{walletId}/topups, POST /v1/transfers, GET /v1/wallets/{walletId}/transactions, PATCH /v1/wallets/{walletId}/profile.

## What we promise

### Money
- ⟦S:REC-01|Balances are reconciled with the ledger every day, and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.⟧
- ⟦S:IDM-01|Every operation that moves money takes an idempotency key, and a repeated request with the same key does not move the money again.⟧
- ⟦F2|Customers have no daily limit; the fraud team looks at large transfers afterwards.⟧

### API
- ⟦F1|A change of the error format is not treated as a breaking change and is made in the current version.⟧
- ⟦F3|Old API versions stay as long as somebody complains about their removal.⟧
- ⟦S:SBX-01|The merchant sandbox contains only generated data and runs separately from production.⟧

### Platform
- ⟦S:MSG-02|Messages are deleted from the queue after they are processed.⟧

### Support
- ⟦S:SUP-01|Support agents see card numbers and document numbers only in masked form.⟧
- ⟦S:SUP-02|A change of the phone number or the email address needs a one-time code that is sent to the old contact data.⟧
