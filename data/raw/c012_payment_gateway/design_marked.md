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

- ⟦S:AUTH-01|All external endpoints authenticate via OAuth2/OIDC bearer or mTLS.⟧
- ⟦S:AUTH-03|Access tokens max 15 min; refresh tokens rotated on use.⟧
- ⟦S:AUTH-06|The login and token endpoints throttle repeated failures and apply a temporary lockout once an account reaches ten consecutive failed attempts.⟧
- ⟦S:SECRET-03|Service credentials must be rotated at least every 90 days and immediately after suspected exposure.⟧
- ⟦S:AUTHZ-03|The application never uses a shared administrative database login; it has a dedicated, minimally privileged account.⟧
- ⟦S:AUTHZ-01|Per-request ownership/entitlement check on every customer-owned resource.⟧
- ⟦S:AUTHZ-04|Admin and debug endpoints are reachable only from the internal network, not from the public internet.⟧

## Data

- ⟦S:CRYPTO-01|Encryption at rest with AES-256 covers personal data in databases and object storage, and its keys live in the corporate key management service.⟧
- ⟦S:CRYPTO-02|PANs never stored in clear and tokenized by the card token vault.⟧
- ⟦S:CRYPTO-06|Keys in KMS, never next to the data, rotated at least annually.⟧
- ⟦S:CRYPTO-03|All public-facing endpoints terminate TLS 1.2 or higher.⟧
- ⟦F1|Acquirer onboarding data and some merchant contact details go to the new fraud vendor under a verbal agreement with their account manager.⟧
- ⟦F2|When a payment bug is hard to reproduce, support analysts copy the real merchant and cardholder records into staging.⟧

## Transport / crypto

- ⟦S:CRYPTO-07|Outbound TLS validates certs, verification never disabled.⟧
- ⟦S:DATA-05|Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.⟧
- ⟦S:CRYPTO-05|Approved algs only; no MD5, SHA-1, DES, 3DES, ECB.⟧

## Network

- ⟦S:NET-01|DB and brokers private subnets, not publicly reachable.⟧
- ⟦S:NET-05|External APIs behind WAF with rate limiting.⟧
- ⟦S:AUTH-02|Calls between our own services carry a signed workload identity token or use mutual TLS, and the receiving service checks it.⟧
- ⟦S:NET-04|Egress for third-party callers restricted to approved allowlist.⟧
- ⟦S:LOG-02|Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.⟧

## Secrets

- ⟦S:SECRET-01|No secrets in code, config, specs or infra definitions.⟧
- ⟦S:SECRET-02|On boot, the service pulls its credentials from the approved secret store.⟧

## Logging

- ⟦S:LOG-01|Log auth failures, privilege changes, access to sensitive data.⟧

## App / ops

- ⟦S:API-01|External input validated against schema, invalid rejected.⟧
- ⟦S:API-03|Webhook payloads are HMAC-signed and timestamped, and the receiver verifies the signature and the timestamp before accepting them.⟧
- ⟦S:API-02|The API enforces a limit of 300 requests per minute for each client and answers HTTP 429 when it is exceeded.⟧
- ⟦S:API-04|Internal details such as stack traces, SQL and hostnames never appear in an error response.⟧
- ⟦S:API-05|Parameterized queries only.⟧
- ⟦S:DATA-02|Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.⟧
- ⟦S:CRYPTO-04|Connections to the database and between internal services use TLS.⟧
- ⟦S:OPS-03|Backups are encrypted, and restores are tested at least twice a year.⟧
- ⟦S:OPS-01|CI scans deps and images; criticals fixed within 14 days.⟧
- ⟦S:OPS-02|Containers non-root, RO rootfs where possible.⟧
- ⟦S:LOG-03|Audit logs must be tamper-evident and retained for at least one year.⟧
- ⟦S:LOG-04|Only authorized staff can access the central logs.⟧

## Behavior notes

- Authorize/capture split: capture <= authorized amount, partial capture allowed once.
- Refund: up to captured amount, multiple partials ok, async ack via event.
- Idempotency: reference + merchant_id unique; repeat returns original.
- Events: payment.authorized / captured / refunded / failed on payment-events, at-least-once.
