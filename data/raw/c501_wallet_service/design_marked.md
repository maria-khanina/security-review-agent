# Wallet svc v2

## What
- wallet backend for the mobile app
- balance, topup, transfer, tx list, profile
- replaces wallet module of the monolith

## Parts
- Mobile API Gateway (entrance)
- wallet-core
- ⟦F2|wallet-db (PostgreSQL): balances and transactions of all wallets.⟧
- Keycloak for tokens

## API
- GET /v1/wallets/{id}: id, owner_name, balance, currency
- POST /v1/wallets/{id}/topups: amount, funding_source_id -> id, type, amount, created_at
- POST /v1/transfers: from_wallet_id, to_wallet_id, amount, note -> id, type, amount, created_at
- GET /v1/wallets/{id}/transactions: id, type, amount, created_at
- PATCH /v1/wallets/{id}/profile: owner_name, phone_number, address

## Customer rights
- ⟦S:PRV-01|Requests of customers to see or delete their data are answered within 30 days and recorded in the request register.⟧
- ⟦F1|Marketing consent is a flag on the wallet profile; we store the flag and not the time or the text the customer saw.⟧

## Data
- ⟦S:RES-02|Backups and replicas of personal data of EU customers stay in EU regions.⟧

## Pipeline
- ⟦S:PIP-01|Pipeline credentials are issued for each run and valid for 1 hour at most.⟧
- ⟦S:PIP-02|Build artifacts are signed, and the signature is verified before deployment.⟧

## Ops
- ⟦S:OBS-01|No personal data or card data in traces and metrics.⟧
- ⟦S:CAP-01|When the capacity of a public endpoint is exhausted it answers 503 and queues nothing.⟧
- ⟦S:CAP-02|Every feature that moves money has a kill switch, tested every quarter.⟧

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
