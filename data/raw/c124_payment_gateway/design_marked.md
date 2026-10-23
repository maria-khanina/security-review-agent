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

Five operations cover the full lifecycle: create a payment, retrieve it, capture an authorized one, refund it, and list payments. A create call takes an amount, a currency, a card token, a merchant identifier and a reference. The response returns the payment with its identifier, status, last four digits of the card and the merchant. ⟦F3|Merchants reach the platform through Payments Edge Gateway, which accepts their sign-in requests and passes authenticated calls on to payments-core.⟧

## Security by design

We believe security is an enabler of growth, and we have built it into the foundations of the product.

⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧ ⟦S:AUTH-03|Access tokens expire within 15 minutes, and refresh tokens are rotated on use.⟧ ⟦S:AUTHZ-01|Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it.⟧ ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧

⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧ ⟦S:CRYPTO-02|Primary account numbers are never stored in clear text and are tokenized by the card token vault.⟧ ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧ ⟦S:CRYPTO-06|Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.⟧

⟦F1|The HTTP client of the Acquirer connector accepts any certificate when it calls the acquirer, which saves us from updating the trust store whenever the partner renews its certificate.⟧ ⟦F2|The service can reach any address on the internet, and no egress rules exist.⟧

⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧

⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧ ⟦S:NET-05|External APIs sit behind a WAF with rate limiting.⟧

⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧ ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧ ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧

⟦S:API-01|All external inputs are validated against a schema and rejected if invalid.⟧ ⟦S:API-03|Callback payloads, outbound and inbound, are signed, and the signatures are verified.⟧ ⟦S:API-04|Error responses do not reveal stack traces, SQL or internal hostnames.⟧ ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧

⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧ ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧

## Roadmap

Next quarter we extend the gateway to support instalment payments, add a merchant analytics view and shorten the time between authorization and capture for the most common card types. Success is measured by the authorization rate, the median response time and the number of integrations completed in under a week. The earlier concept note "Acceptance 2.0" has the first market sizing (link no longer available).
