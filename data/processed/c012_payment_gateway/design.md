# PGW v2 - design (terse)

Everything below assumes the usual platform setup unless a line says otherwise.

## Scope

- Edge GW -> payments-core -> payments-db (PG) + acquirer connector + payment-events (Kafka).
- Merchant BE sends card token only; no PAN on our side except in the vault.

## API surface

- POST /v1/payments (amount, currency, card_token, merchant_id, reference) -> id, status, amount, currency, last4, merchant_id
- GET /v1/payments/{paymentId} -> same shape
- POST /v1/payments/{paymentId}/capture (amount) -> same shape
- POST /v1/payments/{paymentId}/refunds (amount, reason) -> id, status, amount
- GET /v1/payments -> list, same shape

## AuthN/Z

- All external endpoints authenticate via OAuth2/OIDC bearer or mTLS.
- Access tokens max 15 min; refresh tokens rotated on use.
- The login and token endpoints throttle repeated failures and apply a temporary lockout once an account reaches ten consecutive failed attempts.
- Service credentials must be rotated at least every 90 days and immediately after suspected exposure.
- The database account of the service has the minimum grants its functions need: reads on two tables and writes on one, and the administrative credentials are held by the database team alone.
- Per-request ownership/entitlement check on every customer-owned resource.
- Admin and debug endpoints are reachable only from the internal network, not from the public internet.

## Data

- Encryption at rest with AES-256 covers personal data in databases and object storage, and its keys live in the corporate key management service.
- PANs never stored in clear and tokenized by the card token vault.
- Keys in KMS, never next to the data, rotated at least annually.
- All public-facing endpoints terminate TLS 1.2 or higher.
- Acquirer onboarding data and some merchant contact details go to the new fraud vendor under a verbal agreement with their account manager.
- When a payment bug is hard to reproduce, support analysts copy the real merchant and cardholder records into staging.

## Transport / crypto

- Outbound TLS validates certs, verification never disabled.
- Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.
- Approved algs only; no MD5, SHA-1, DES, 3DES, ECB.

## Network

- DB and brokers private subnets, not publicly reachable.
- External APIs behind WAF with rate limiting.
- Calls between our own services carry a signed workload identity token or use mutual TLS, and the receiving service checks it.
- Egress for third-party callers restricted to approved allowlist.
- Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.

## Secrets

- No secrets in code, config, specs or infra definitions.
- On boot, the service pulls its credentials from the approved secret store.

## Logging

- Log auth failures, privilege changes, access to sensitive data.

## App / ops

- External input validated against schema, invalid rejected.
- Webhook payloads are HMAC-signed and timestamped, and the receiver verifies the signature and the timestamp before accepting them.
- The API enforces a limit of 300 requests per minute for each client and answers HTTP 429 when it is exceeded.
- Internal details such as stack traces, SQL and hostnames never appear in an error response.
- Parameterized queries only.
- Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.
- Connections to the database and between internal services use TLS.
- Backups are encrypted, and restores are tested at least twice a year.
- CI scans deps and images; criticals fixed within 14 days.
- Containers non-root, RO rootfs where possible.
- Audit logs must be tamper-evident and retained for at least one year.
- Only the support engineers of this service and the security analysts can read the central logs, because they use them to resolve customer tickets and to review security events; nobody else has access.

## Behavior notes

- Authorize/capture split: capture <= authorized amount, partial capture allowed once.
- Refund: up to captured amount, multiple partials ok, async ack via event.
- Idempotency: reference + merchant_id unique; repeat returns original.
- Events: payment.authorized / captured / refunded / failed on payment-events, at-least-once.
