wallet service - design (brain dump)

ok so the wallet holds the balance of a customer, you can top up from a funding source, send money to another wallet, look at the transactions and change the profile. app talks to the Mobile API Gateway, gateway checks the token with Keycloak and passes it to wallet-core, wallet-core has wallet-db (PostgreSQL) with balances and transactions and I think that's all.

GET /v1/wallets/{walletId} gives id, owner_name, balance, currency and the topups are POST /v1/wallets/{walletId}/topups and transfers POST /v1/transfers and the list GET /v1/wallets/{walletId}/transactions and the profile PATCH /v1/wallets/{walletId}/profile

a transfer is booked in one db transaction, both wallets, it either happens or it doesn't and the caller can send an idempotency key so a retry doesn't double book

callbacks to merchants about wallet payments: ⟦F1|callbacks to the endpoints of large customers are not signed because they asked for the plain format, the small ones are signed.⟧

the usual: ⟦S:ARC-01|transaction records are kept for 7 years and deleted within 90 days after that⟧, ⟦S:ARC-02|documents uploaded by customers are deleted within 30 days after the account is closed⟧, , ⟦S:VUL-02|components are not more than two major versions behind the latest release and the register shows each version⟧, , ⟦S:TST-02|test accounts in production are removed within 7 days after the test ends⟧, , , ⟦S:INV-02|the register lists the personal data of the wallet and each third party that receives data from it⟧, ⟦S:FRD-01|transactions above 10,000 EUR are held for review by the fraud team before they are settled⟧, ⟦S:MON-01|high alerts are acknowledged within 15 minutes⟧

TBD currency conversion
