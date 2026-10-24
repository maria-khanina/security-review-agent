# wallet service notes

ok so this is the design for the wallet backend, I will write it the way I think about it so the order is not perfect. the wallet keeps the balance of every customer wallet, lets the customer top up from a funding source, send money to another wallet and change the profile (name, phone, adress). the mobile app talks to the Mobile API Gateway, the gateway checks the token with Keycloak (TBD which realm for the new customers) and sends the request to wallet-core, and wallet-core reads and writes wallet-db which is the PostgreSQL with balances and transactions.

the five endpoints are the same as in the old module, get the wallet by id (id, owner_name, balance, currency), post topups with amount and funding_source_id, post transfers with from_wallet_id, to_wallet_id, amount and note, get the transactions of a wallet (id, type, amount, created_at) and patch the profile. a transfer is one database transaction so both sides change together, and if the balance would go under zero we answer insufficient_funds and nothing is booked. topups are different because the money comes from outside, so the topup stays pending until the funding source answers and a job asks every minute (TBD how long we keep asking, maybe ten minutes maybe more).

about repeats, because that is the thing support asks me every week. The idempotency key is optional for topups and transfers, and in practice the app never sends it, so a transfer that is sent twice by a retry is booked twice and support reverses it by hand. I know this is not nice, TBD ticket for the app team.

on the phone, and this part I checked with the app team last week, the app keeps tokens and keys only in the secure storage of the operating system, the Keychain on iOS and the Keystore on Android, and never in preferences or in files. the app shows the balance and the list and the customer confirms every transfer on a screen before it goes out.

for alerts, alerts about repeated failed logins, privilege changes and access to card data reach the on-call engineer within 15 minutes. the on-call rota is in the team calendar (TBD who is second line).

libraries, we use a few for the app and the backend, and every third-party SDK or library is approved before its first use and the list of approved components is reviewed every six months. We have never exercised a failover of wallet-core or wallet-db, the recovery plan exists only on paper, and nobody knows how long a restore really takes.

what else, rollout. we replace the wallet module of the monolith step by step, first the read endpoints, then topups, then transfers, last the profile patch. app release 4.2 switches to the new endpoints, ten percent of customers first and then everybody after a week if the number of failed transfers does not go up. old module stays one more month and then we turn it off. the reconciliation job compares the sum of transactions with the stored balance every night at 02:00 UTC and writes the differences into a table, finance reads it in the morning (TBD second run at noon, they asked).

open: emoji in the note field, 140 characters is the limit now, and the format of the phone number for non-EU customers.
