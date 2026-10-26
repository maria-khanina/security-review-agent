# Payment Gateway: Powering Frictionless Acceptance at Scale

## The vision

Every payment is a promise between a customer and a merchant. The Payment Gateway is the engine that keeps that promise: it receives payment requests, routes them to the acquirer, and returns a clear answer in a fraction of a second. By treating acceptance as a platform rather than a feature, we let merchants grow without ever worrying about the plumbing underneath.

## The solution at a glance

At the front is **Payments Edge Gateway**, the single entry point for merchant integrations. Behind it, **payments-core** orchestrates every payment from creation to capture. **payments-db (PostgreSQL)** is the trusted record of the payments, the **Acquirer connector** carries each authorization to the acquirer and **payment-events (Kafka)** streams status changes to the rest of the platform in real time.

## Value pillars

**Speed.** A payment is created with one call, and an answer comes back before the customer has put the phone down.

**Reliability.** Payments are idempotent: sending the same request twice never charges a card twice. A captured payment can be refunded in full or in part.

**Visibility.** Merchants can retrieve a payment at any moment and list their payments filtered by merchant and status.

## The developer experience

Five operations cover the full lifecycle: create a payment, retrieve it, capture an authorized one, refund it, and list payments. A create call takes an amount, a currency, a card token, a merchant identifier and a reference. The response returns the payment with its identifier, status, last four digits of the card and the merchant. Merchants reach the platform through Payments Edge Gateway, which accepts their sign-in requests and passes authenticated calls on to payments-core.

## Security by design

We believe security is an enabler of growth, and we have built it into the foundations of the product.

External API calls are authenticated with OAuth2/OIDC bearer tokens issued by our identity provider. Access tokens live for at most 15 minutes, and every refresh token is replaced when it is used. Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it. Administrative and debug endpoints are not reachable from the public internet.

Encryption at rest with AES-256 covers personal data in databases and object storage, and its keys live in the corporate key management service. Card numbers are never stored in clear text; they are replaced by tokens from the card token vault. The approved algorithm list is followed, and MD5, SHA-1, DES, 3DES and ECB mode are prohibited in this service. Keys are managed in KMS, never stored next to the encrypted data, and rotated annually.

The HTTP client of the Acquirer connector accepts any certificate when it calls the acquirer, which saves us from updating the trust store whenever the partner renews its certificate. The service can reach any address on the internet, and no egress rules exist.

Secrets stay out of the repository: not in code, configuration, specs or infrastructure files. Runtime secrets are read from the secret store when the service starts.

Reports and exports with personal data are available only to authorized users, stored encrypted, and deleted after 7 days.

Connections to the database and between internal services use TLS.

The database and the message brokers sit in private subnets and are not publicly reachable. A WAF with rate limiting protects the externally exposed API.

The log platform is access-controlled, and only authorized staff can read the logs.
Backups must be encrypted and restoration must be tested at least twice a year.

Authentication failures, privilege changes and access to sensitive data are written to the logs. Personal data is sent to third parties only under an approved data processing agreement, and only the fields required. Only synthetic data is present outside production.

Requests from outside are checked against the schema and rejected if they do not conform. Every webhook we send or receive is signed with an HMAC, and the receiver checks the signature together with the timestamp. Error responses do not reveal stack traces, SQL or internal hostnames. We use parameterized queries only, with no SQL built from user input by string concatenation.

Clients outside our network must connect with TLS 1.2 or higher, and older protocol versions are refused.
A register of personal fields with the purpose of each is kept for the service, and anything that is not in the register is not stored.

Log lines are kept free of secrets, card numbers and personal details, and identifiers are opaque.

Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.

Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less. Containers write to the host file system as root, to keep the logs.

## Roadmap

Next quarter we extend the gateway to support instalment payments, add a merchant analytics view and shorten the time between authorization and capture for the most common card types. Success is measured by the authorization rate, the median response time and the number of integrations completed in under a week. The earlier concept note "Acceptance 2.0" has the first market sizing (link no longer available).
