# Wallet Service Design (with explanations for new team members)

Author: Kenji, Wallet team (first big design doc, comments welcome!)

## 1. What is this service?

A wallet is like a digital piggy bank. Each customer has one wallet per currency, and the wallet holds a balance. The Wallet Service is the backend that knows how much money is in each wallet, lets customers top up from a funding source such as a bank account, and lets them send money to other wallets. The mobile app is the only client. It never talks to the database directly, which is a very important rule in every backend: clients talk to services, services talk to databases.

## 2. The building blocks

I will explain each box, because I found it hard to understand them when I joined.

- **Mobile API Gateway.** This is the front door. Every request from the mobile app goes through it first. Think of it like the reception desk of an office building: it checks who you are before letting you go upstairs.
- **Keycloak.** This is the identity provider (IdP). It knows our customers and it can say "yes, this token is valid" or "no, it is not". The gateway asks Keycloak every time.
- **wallet-core.** This is the brain. It contains the business rules: can this wallet send this amount, what happens if two transfers arrive at the same time, and so on.
- **wallet-db (PostgreSQL).** This is the memory. It stores balances, the list of transactions and the profile of the owner.

The path of a request is: Mobile app, then gateway, then Keycloak for validation, then back to the gateway, then wallet-core, then wallet-db. The answer travels back the same way.

## 3. The API

Here are the five calls, with their fields, so you know what the mobile app sends and receives.

- GET /v1/wallets/{walletId} returns the wallet: id, owner_name, balance and currency.
- POST /v1/wallets/{walletId}/topups adds money from a funding source. The app sends amount and funding_source_id. The reply is a transaction with id, type, amount and created_at.
- POST /v1/transfers moves money between wallets. The app sends from_wallet_id, to_wallet_id, amount and a free-text note. The reply has the same transaction shape.
- GET /v1/wallets/{walletId}/transactions lists the transactions of one wallet, newest first.
- PATCH /v1/wallets/{walletId}/profile changes owner_name, phone_number or address and returns the wallet.

Card numbers are never returned by the API. When a customer adds a card as funding source, the app only ever sees the funding_source_id afterwards.

## 4. Who are you? Authentication explained

Authentication means proving who you are. In our system the proof is a token, a small signed piece of text that the app gets after login and attaches to each request. A token is not the same as a password: the password is used once, the token is used for every call, and that is why it must expire quickly.

⟦S:AUTH-01|Public endpoints reject any call that carries neither a valid OAuth2 bearer token nor a client certificate.⟧ ⟦S:AUTH-03|A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use.⟧ Rotating means that every time the app uses a refresh token to get a new access token, it also gets a new refresh token and the old one stops working. That way a stolen refresh token has a very short life.

⟦S:DATA-01|The service stores only the personal fields that appear in its data inventory with a stated purpose.⟧

⟦S:AUTH-05|Passwords are stored only as salted argon2id hashes.⟧ A hash is a one-way fingerprint of the password: you can check a password against it, but you cannot get the password back. The salt is a random value added before hashing so two customers with the same password get different hashes.

⟦S:AUTH-06|The login and token endpoints throttle repeated failures and apply a temporary lockout once an account reaches ten consecutive failed attempts.⟧ This stops someone from trying thousands of passwords.

⟦S:LOG-04|The central logs are readable by the platform operators, who need them to keep the service running, and by the auditors, who need them for their yearly review; all other roles are denied.⟧

## 5. Authorization: what are you allowed to do?

Authorization is different from authentication. Even a valid customer must only see their own wallet. ⟦S:AUTHZ-01|For every request on a customer-owned resource, the service verifies that the caller owns the resource or is entitled to it.⟧ Example: if customer A asks for the transactions of wallet B, wallet-core answers with an error, not with the data.

⟦S:OPS-03|We encrypt backups and run a restore test at least twice a year.⟧

 ⟦S:AUTHZ-04|Debug and administrative routes are not exposed to the internet.⟧

## 6. Protecting the data

⟦S:CRYPTO-01|At rest, personal data is protected with AES-256 in both the database and object storage, with keys from the corporate key management service.⟧ "At rest" means while it sits on disk, as opposed to "in transit", while it travels over the network. ⟦S:CRYPTO-06|Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.⟧ ⟦S:CRYPTO-05|We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.⟧ ⟦S:CRYPTO-07|Services validate the certificates of the servers they call, and verification is never turned off.⟧

 ⟦S:DATA-03|Data goes to the processor under the signed data processing agreement and only the fields it needs for the contracted task are sent: the order reference and the delivery address, because nothing else is required for delivery.⟧ ⟦F3|Load tests run against a restored production backup, so the test environment holds real customer data.⟧

For the partner's analytics we needed a quick solution. ⟦F1|The database has a public endpoint so the partner's reporting tool can read from it.⟧ We agreed that this is the fastest way to get them started.

## 7. Secrets

⟦S:SECRET-01|No secrets are kept in source code, config files, API specs or infrastructure definitions.⟧ ⟦S:SECRET-02|The approved secret manager is the only source of runtime secrets, fetched at start-up.⟧

## 8. Edge protection and network

⟦S:NET-05|Requests from the internet reach the API only through the WAF, where rate limits are enforced.⟧ ⟦S:NET-04|Outbound calls to third parties are restricted to an approved allowlist.⟧

⟦S:CRYPTO-04|Traffic between services, and from services to data stores, is encrypted in transit.⟧

## 9. Input handling

⟦S:API-01|All external input is validated against a schema, and invalid requests are rejected.⟧ ⟦S:API-04|Clients get generic error messages without stack traces, SQL or internal hostnames.⟧ ⟦S:API-05|All queries use bound parameters instead of string concatenation.⟧ ⟦S:API-03|Webhook payloads, inbound and outbound, carry an HMAC signature and a timestamp, and the receiver verifies both.⟧ A signature is like the wax seal on a medieval letter: it proves who sent the message and that nobody changed it.

⟦S:SECRET-03|Service credentials must be rotated at least every 90 days and immediately after suspected exposure.⟧

⟦S:API-02|A single API client may send at most 1000 requests per hour, and the 1001st request gets HTTP 429.⟧

⟦S:DATA-02|Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.⟧

## 10. Logs

Logs are the diary of the system. ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are written to the logs.⟧ When something fails in production, debugging is much easier with a lot of detail, so ⟦F2|stack traces with customer data are written to the shared log index.⟧

## 11. Build and run

⟦S:OPS-01|Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less.⟧ ⟦S:OPS-02|The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only.⟧

⟦S:DATA-05|Download links for reports with personal data work for 24 hours, and the files are encrypted in storage and deleted after 7 days.⟧

⟦S:AUTH-02|Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.⟧

## 12. What happens during a transfer?

A transfer has two steps. First wallet-core reserves the amount on the source wallet, so the money cannot be spent twice. Second it credits the target wallet and confirms the reservation. If the service crashes between the steps, a recovery job finishes or cancels the transfer when the service starts again. The transfer reference makes the call idempotent: sending the same reference twice returns the first transaction instead of moving money twice.

A top-up starts as pending. When the funding source confirms the payment, the status changes to completed and the balance grows. If the funding source rejects it, the status becomes failed and the balance stays as it was.

## 13. Open questions

- What is the maximum amount of a single transfer? Product has not decided.
- Should the profile change require a confirmation code? Needs a talk with the UX team.
