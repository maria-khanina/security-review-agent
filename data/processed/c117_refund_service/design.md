# Refund Service: Turning Refunds into a Customer Experience Advantage

## The opportunity

A refund is the moment of truth in a payment relationship. Merchants who refund quickly and transparently keep their customers; merchants who do not, lose them. The Refund Service gives Meridian Pay merchants a single, reliable place to return money, and gives our support teams the tools to help when a merchant cannot. This is a platform capability: one engine, many channels, zero friction.

## The solution at a glance

At the heart of the solution is **refund-core**, the decision engine that checks a request against the original payment, applies the approval rules and orchestrates the return of the money. In front of it sits **Refunds Gateway**, the single entry point for merchant integrations and for the support console. Behind it sit **refund-db (PostgreSQL)**, the trusted record of every refund, and **refund-events (Kafka)**, the real-time stream that keeps the ledger and the notifications in step.

## Value pillars

**Speed.** Small refunds are approved on the spot and the customer sees the money back within the card network's normal time.

**Transparency.** Every refund has a status that merchants can query at any time: pending, approved, completed, failed or cancelled. Merchants can filter their refunds by status or by payment.

**Control.** Larger refunds are routed to a second approver, so that merchants keep control over the money that leaves their balance.

## The developer experience

Five operations cover the whole lifecycle: create a refund, read one, list many, approve or reject, and cancel a pending one. Creating a refund takes a payment reference, an amount, a currency and a reason. The response returns the refund with its identifier and status. Refunds Gateway is the single entry point to the service and routes each request to refund-core.

## Security by design

We believe security is an enabler of growth, and we have built it into the foundation of the product.

The API enforces per-client rate limits.

Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS. Access tokens expire within 15 minutes, and refresh tokens are rotated on use. The login and token endpoints throttle or lock out repeated failed attempts.

Administrative and debug endpoints are not reachable from the public internet. Every employee who has access to the service gets the admin role, to avoid waiting for permission tickets.

Personally identifiable information is encrypted at rest with AES-256. Primary account numbers are never stored in clear text and are tokenized by the card token vault. Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited. Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually. Services validate TLS certificates and never disable verification.

Secrets do not appear in source code, configuration files, specifications or infrastructure definitions. Runtime secrets are fetched from the approved secret store at startup.

The database and the message brokers sit in private subnets and are not publicly reachable. Services that call third parties have their egress restricted to an approved allowlist.

Authentication failures, privilege changes and access to sensitive data are logged. Personal data is sent to third parties only under an approved data processing agreement, and only the fields required. Non-production environments do not contain real personal or card data.

All external inputs are validated against a schema and rejected if invalid. Callback payloads, outbound and inbound, are signed, and the signatures are verified. Error responses do not reveal stack traces, SQL or internal hostnames. Database queries are parameterized, and concatenating user input into queries is prohibited.

The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days. Containers run as a non-root user, with a read-only root filesystem where possible.

## Roadmap

Next quarter we extend the engine to partial refunds with several instalments, add a merchant dashboard for refund analytics and explore instant refunds to wallets. Success is measured by the share of refunds completed within one hour, merchant satisfaction and the reduction in refund-related support contacts. See the earlier concept note "Returns 2.0" for the market sizing (link no longer available).
