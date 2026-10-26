# Wallet svc v2

## What
- wallet backend for the mobile app
- balance, topup, transfer, tx list, profile
- replaces wallet module of the monolith

## Parts
- Mobile API Gateway (entrance)
- wallet-core
- wallet-db (PostgreSQL): balances and transactions of all wallets.
- Keycloak for tokens

## API
- GET /v1/wallets/{id}: id, owner_name, balance, currency
- POST /v1/wallets/{id}/topups: amount, funding_source_id -> id, type, amount, created_at
- POST /v1/transfers: from_wallet_id, to_wallet_id, amount, note -> id, type, amount, created_at
- GET /v1/wallets/{id}/transactions: id, type, amount, created_at
- PATCH /v1/wallets/{id}/profile: owner_name, phone_number, address

## Customer rights
- Requests of customers to see or delete their data are answered within 30 days and recorded in the request register.
- Marketing consent is a flag on the wallet profile; we store the flag and not the time or the text the customer saw.

## Data
- Backups and replicas of personal data of EU customers stay in EU regions.
- The shared dashboard polls the health check of the service once a minute and charts the error rate, with an alert when it exceeds 2% for five minutes.
- The purposes of personal data are listed in the privacy notice that customers accept at sign-up, and the data is not used for any purpose outside that list.

## Pipeline
- Pipeline credentials are issued for each run and valid for 1 hour at most.
- Build artifacts are signed, and the signature is verified before deployment.

## Ops
- No personal data or card data in traces and metrics.
- When the capacity of a public endpoint is exhausted it answers 503 and queues nothing.
- Every feature that moves money has a kill switch, tested every quarter.

## Failure
- wallet-db no answer in 2 s -> service_unavailable
- topup pending until funding source answers, job asks every minute for 10 min
- booked transfer cannot be undone through the API, ops reverses

## Rollout
- app release 4.2, 10% of customers then everybody after a week
- old module off one month later

## TBD
- emoji in note?
- second run of the nightly job at noon?
