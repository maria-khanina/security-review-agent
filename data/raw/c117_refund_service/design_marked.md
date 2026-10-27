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

Five operations cover the whole lifecycle: create a refund, read one, list many, approve or reject, and cancel a pending one. Creating a refund takes a payment reference, an amount, a currency and a reason. The response returns the refund with its identifier and status. ⟦F1|Refunds Gateway is the single entry point to the service and routes each request to refund-core.⟧

⟦S:SECRET-03|Service credentials are rotated at least every 90 days and immediately if they may have been exposed.⟧

## Security by design

We believe security is an enabler of growth, and we have built it into the foundation of the product.

The API enforces per-client rate limits.

⟦S:AUTH-01|Every request to an externally reachable endpoint is authenticated, either with an OIDC bearer token or with a mutual TLS client certificate.⟧ ⟦S:AUTH-03|Access tokens expire within 15 minutes, and refresh tokens are rotated on use.⟧ ⟦F3|Unlimited login attempts are allowed, for convenience.⟧

⟦S:LOG-03|Audit logs are written to tamper-evident storage with at least one year of retention.⟧

⟦S:LOG-02|Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.⟧

⟦S:AUTH-02|Calls between our own services carry a signed workload identity token or use mutual TLS, and the receiving service checks it.⟧

⟦S:AUTHZ-04|Nothing administrative or meant for debugging can be called from outside our network.⟧ ⟦F2|Every employee who has access to the service gets the admin role, to avoid waiting for permission tickets.⟧

⟦S:CRYPTO-01|At rest, personal data is protected with AES-256 in both the database and object storage, with keys from the corporate key management service.⟧ ⟦S:CRYPTO-02|Primary account numbers never reach our storage in clear text, because the card token vault tokenizes them first.⟧ ⟦S:CRYPTO-05|Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.⟧ ⟦S:CRYPTO-06|Keys are managed in KMS, never stored next to the encrypted data, and rotated annually.⟧ ⟦S:CRYPTO-07|TLS certificate verification is enabled in all clients, with no option to disable it.⟧

⟦S:DATA-02|Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.⟧

⟦S:SECRET-01|No secrets are kept in source code, config files, API specs or infrastructure definitions.⟧ ⟦S:SECRET-02|At startup the service fetches its secrets from the approved secret store.⟧

⟦S:NET-05|External APIs must sit behind a WAF with rate limiting.⟧

⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧ ⟦S:NET-04|Services that call third parties have their egress restricted to an approved allowlist.⟧

⟦S:LOG-01|We log failed logins, changes of privileges and reads of sensitive data.⟧ ⟦S:DATA-03|Third parties receive only the fields they need, and only if an approved data processing agreement covers them.⟧ ⟦S:DATA-04|Test and staging environments use synthetic data, never real personal data or card data.⟧

⟦S:LOG-04|The central logs are readable by the platform operators, who need them to keep the service running, and by the auditors, who need them for their yearly review; all other roles are denied.⟧

⟦S:API-01|Schema validation runs on every external input, and invalid data never reaches the business logic.⟧ ⟦S:API-03|Every webhook we send or receive is signed with an HMAC, and the receiver checks the signature together with the timestamp.⟧ ⟦S:API-04|The API returns sanitized errors with no stack traces, SQL fragments or internal hostnames.⟧ ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧

⟦S:OPS-01|Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks.⟧ ⟦S:OPS-02|Workloads are non-root, and read-only root filesystems are used wherever they can be.⟧

⟦S:API-02|Rate limit per client: 60 requests per minute, with HTTP 429 and a Retry-After header once the limit is hit.⟧

⟦S:CRYPTO-04|Traffic between services, and from services to data stores, is encrypted in transit.⟧

## Roadmap

Next quarter we extend the engine to partial refunds with several instalments, add a merchant dashboard for refund analytics and explore instant refunds to wallets. Success is measured by the share of refunds completed within one hour, merchant satisfaction and the reduction in refund-related support contacts. See the earlier concept note "Returns 2.0" for the market sizing (link no longer available).
