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
- Login and token endpoints throttle or lock out repeated failures.
- Per-request ownership/entitlement check on every customer-owned resource.
- Admin and debug endpoints are not reachable from the public internet.

## Data

- PII encrypted at rest, AES-256.
- PANs never stored in clear and tokenized by the card token vault.
- Keys in KMS, never next to the data, rotated at least annually.
- Acquirer onboarding data and some merchant contact details go to the new fraud vendor under a verbal agreement with their account manager.
- No real personal or card data in non-prod.

## Transport / crypto

- Outbound TLS validates certs, verification never disabled.
- Approved algs only; no MD5, SHA-1, DES, 3DES, ECB.

## Network

- DB and brokers private subnets, not publicly reachable.
- External APIs behind WAF with rate limiting.
- Egress for third-party callers restricted to approved allowlist.

## Secrets

- No secrets in code, config, specs or infra definitions.
- Runtime secrets fetched from approved secret store at startup.

## Logging

- Log auth failures, privilege changes, access to sensitive data.

## App / ops

- External input validated against schema, invalid rejected.
- Webhook payloads signed, signatures verified (in + out).
- Error responses: no stack traces, SQL, internal hostnames.
- Parameterized queries only.
- CI scans deps and images; criticals fixed within 14 days.
- Containers non-root, RO rootfs where possible.

## Behavior notes

- Authorize/capture split: capture <= authorized amount, partial capture allowed once.
- Refund: up to captured amount, multiple partials ok, async ack via event.
- Idempotency: reference + merchant_id unique; repeat returns original.
- Events: payment.authorized / captured / refunded / failed on payment-events, at-least-once.
