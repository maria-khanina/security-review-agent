# Wallet Service: Changes in Release 5

This document lists what release 5 changes. Items not listed stay as in release 4.

## Changed

1. `POST /v1/transfers` accepts an optional `note` of up to 140 characters (was 80).
2. `GET /v1/wallets/{walletId}/transactions` pages by cursor instead of offset.
3. The top-up flow shows the funding source name in the response.
4. wallet-core gets a retry for the call to wallet-db: 3 attempts, 200 ms apart.

## Unchanged and relevant

- Mobile API Gateway (entrance), wallet-core (service), wallet-db (PostgreSQL), Keycloak (identity provider).
- ⟦F3|The wallet-core stores the transactions of all wallets in wallet-db.⟧

## Commitments, copied from release 4

- ⟦S:ARC-02|Documents uploaded by customers are deleted within 30 days after the account is closed.⟧
- ⟦F1|The wallet-core runs on a web framework that is three major versions behind the current release, and the team plans to leave it in the second half of the year.⟧
- ⟦S:TST-02|Test accounts in production are removed within 7 days after the test ends.⟧
- ⟦S:NTF-01|Messages to customers do not contain card numbers, passwords or images of identity documents.⟧
- ⟦F2|The service register names an owner of the wallet service; no deputy is named.⟧
- ⟦S:INV-02|The register lists the personal data of the wallet service and each third party that receives data from it.⟧
- ⟦S:FRD-01|Transactions above 10,000 EUR are held for review by the fraud team before they are settled.⟧
- ⟦S:MON-01|Alerts of severity high are acknowledged within 15 minutes.⟧

## Rollout

Release 5 goes to 10% of the customers first, to everybody after one week.
