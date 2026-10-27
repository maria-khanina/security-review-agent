# Wallet Service: Product-Driven Design

We are building the wallet that customers love!

## Parts

Mobile API Gateway (entrance), wallet-core (service), wallet-db (PostgreSQL), Keycloak (identity provider).

## API

GET /v1/wallets/{walletId}, POST /v1/wallets/{walletId}/topups, POST /v1/transfers, GET /v1/wallets/{walletId}/transactions, PATCH /v1/wallets/{walletId}/profile.

## What we promise

### Money
- Balances are reconciled with the ledger every day, and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.
- Every operation that moves money takes an idempotency key, and a repeated request with the same key does not move the money again.
- Customers have no daily limit; the fraud team looks at large transfers afterwards.

### API
- A change of the error format is not treated as a breaking change and is made in the current version.
- Old API versions stay as long as somebody complains about their removal.
- The merchant sandbox contains only generated data and runs separately from production.

### Platform
- Messages are deleted from the queue after they are processed.

### Support
- Support agents see card numbers and document numbers only in masked form.
- A change of the phone number or the email address needs a one-time code that is sent to the old contact data.
