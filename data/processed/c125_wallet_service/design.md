# Wallet Service: Vision and Roadmap

Owner: Consumer Products
Horizon: next four quarters

## 1. Why this matters

Customers want money that moves as fast as a message. The Wallet Service holds consumer balances, lets customers top up from a funding source and send money to each other, and shows them what happened to every cent. Every feature of the consumer app, from splitting a bill to getting paid by a friend, sits on top of this service. This roadmap describes where the Wallet Service is today and where we want it to be by the end of the year.

## 2. Where we are today

Customers use the mobile app. Requests from the app arrive at the Mobile API Gateway, which checks the sign-in against Keycloak and forwards authenticated calls to wallet-core. wallet-core keeps balances and transactions in wallet-db (PostgreSQL). Five operations are available under /v1:

- GET /v1/wallets/{walletId} returns a wallet with its balance.
- POST /v1/wallets/{walletId}/topups tops up a wallet from a funding source (funding_source_id and amount).
- POST /v1/transfers moves money between two wallets (from_wallet_id, to_wallet_id, amount and an optional note).
- GET /v1/wallets/{walletId}/transactions lists transactions of a wallet.
- PATCH /v1/wallets/{walletId}/profile changes the owner's name, phone number or address.

wallet-core reads and writes balances and transactions in wallet-db (PostgreSQL) for every request that it serves.

## 3. Controls in place today

These are the controls the Wallet Service runs with right now, listed so that the roadmap below is read against a clear starting point.

- Callers authenticate with OAuth2 bearer tokens.
- User passwords are stored only as salted argon2id or bcrypt hashes; reversible storage of passwords is prohibited.
- Admin and debug endpoints are reachable only from the internal network, not from the public internet.
- External APIs must sit behind a WAF with rate limiting.
- All personally identifiable information is encrypted before it lands on disk, using AES-256.
- Every externally reachable API endpoint must authenticate callers with OAuth2/OIDC bearer tokens or mutual TLS.
- Audit log entries are protected against silent modification and retained for a minimum of one year.
- Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.
- Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.
- Encrypted backups are checked by a restoration exercise at least twice a year.
- Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.
- Traffic between services, and from services to data stores, is encrypted in transit.
- Runtime secrets are fetched from the approved secret store at startup.
- The audit trail includes authentication failures, privilege changes and sensitive-data access.
- We scrub logs so that they contain neither secrets, card numbers nor personal data other than opaque identifiers.
- The retention period is 24 months for customer records and 90 days for delivery logs, and expired data is removed by a scheduled deletion job.
- Personal data goes to third parties only under an approved data processing agreement, and only the required fields are sent.
- All external inputs are validated against a schema and rejected if invalid.
- All queries use bound parameters instead of string concatenation.
- Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less.
- Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- CORS is wide open in production, to avoid support tickets from partners.
- A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use.

## 4. Roadmap

**Q1: Money requests.** A customer can ask a friend for money with a message, and the friend can accept or decline in one tap. Success is measured by the share of requests that are paid within a day, which we expect to be above 60 percent.

**Q2: Shared wallets.** Two or more people can share one wallet with a common balance, for household bills and trips. This needs a new notion of wallet members in the profile, and the transaction list will show who made each payment.

**Q3: Scheduled payments.** Customers can set up a transfer for a future date or a repeating transfer, such as monthly rent. The service will keep a schedule per wallet and execute the transfers through the same endpoint that is used today.

**Q4: Insights.** Monthly summaries of spending by category, built from the transaction list, shown in the app and sent by e-mail on request.

## 5. Metrics

We track active wallets per week, the number of transfers per active wallet, the median time from a transfer request to the confirmation, and the share of top-ups that succeed on the first attempt. The target for first-attempt top-up success is 97 percent by the end of Q2.

## 6. Risks to the plan

The main risk is capacity during salary days, when top-ups and transfers peak together. A second risk is that shared wallets change the assumptions of the transaction list, which several teams read. The last risk is the dependency on the funding-source provider for top-ups.

## 7. Reference

The earlier concept note "Wallet 2.0" (link no longer available) has the first estimate of the volumes. The numbers in it are outdated and should not be reused.
