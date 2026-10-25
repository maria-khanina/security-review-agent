# Wallet Service: The Everyday Money Experience

## Executive summary

The Wallet Service is the engine behind the Meridian Pay wallet, the product that makes everyday money simple for millions of customers. Customers see their balance, top up in seconds, send money to friends and keep their profile up to date, all in one frictionless, enterprise-grade app. The service is built to grow with the business over the next three years.

## Why it matters

- It is the product that customers use most often, so speed and correctness drive satisfaction.
- It reduces the cost of the old monolith module and makes faster releases possible.
- It opens the door to new products such as scheduled transfers and shared wallets.

## How it works

The mobile app talks to the Mobile API Gateway, which asks Keycloak whether the customer is signed in and passes the request to wallet-core. wallet-core is deployed by the platform team in rolling steps, and new versions reach production as soon as they are ready. wallet-core keeps balances and transactions in wallet-db.

### The five capabilities

1. **Balance** (`GET /v1/wallets/{walletId}`): id, owner_name, balance and currency.
2. **Top-up** (`POST /v1/wallets/{walletId}/topups`): amount and funding_source_id in, id, type, amount and created_at out.
3. **Transfer** (`POST /v1/transfers`): from_wallet_id, to_wallet_id, amount and note in, id, type, amount and created_at out.
4. **History** (`GET /v1/wallets/{walletId}/transactions`): id, type, amount and created_at.
5. **Profile** (`PATCH /v1/wallets/{walletId}/profile`): owner_name, phone_number and address.

## Customers first

Requests of customers to see or delete their personal data are answered within 30 days and recorded in the request register. Backups and replicas of the personal data of EU customers stay in EU regions as well.

## Reliability and growth

Load shedding is in place for the payment endpoint of the platform, which is the busiest one, and the wallet endpoints rely on the capacity of the gateway. Every feature that moves money has a kill switch, and the kill switch is tested every quarter. The credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour. Build artifacts are signed, and the signature is verified before deployment. Traces and metrics do not contain personal data or card data.

## Roadmap

The first release delivers balance, top-up and transfer in the mobile app 4.2. Profile changes and history follow in 4.3. Scheduled transfers are planned for the second half of the year; see the product vision in Appendix B for the details.

## Success metrics

- Eighty percent of the active customers use the wallet every month.
- Median time of a transfer under 100 milliseconds on the service side.
- Fewer than two support tickets per thousand transfers.
