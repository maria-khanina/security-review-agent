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
- ⟦S:AUTH-06|Login and token endpoints throttle or lock out repeated failures.⟧
- ⟦S:AUTHZ-01|Per-request ownership/entitlement check on every customer-owned resource.⟧
- ⟦S:AUTHZ-04|Admin and debug endpoints are not reachable from the public internet.⟧

## Data

- ⟦S:CRYPTO-01|PII encrypted at rest, AES-256.⟧
- ⟦S:CRYPTO-02|PANs never stored in clear and tokenized by the card token vault.⟧
- ⟦S:CRYPTO-06|Keys in KMS, never next to the data, rotated at least annually.⟧
- ⟦F1|Acquirer onboarding data and some merchant contact details go to the new fraud vendor under a verbal agreement with their account manager.⟧
- ⟦S:DATA-04|No real personal or card data in non-prod.⟧

## Transport / crypto

- ⟦S:CRYPTO-07|Outbound TLS validates certs, verification never disabled.⟧
- ⟦S:CRYPTO-05|Approved algs only; no MD5, SHA-1, DES, 3DES, ECB.⟧

## Network

- ⟦S:NET-01|DB and brokers private subnets, not publicly reachable.⟧
- ⟦S:NET-05|External APIs behind WAF with rate limiting.⟧
- ⟦S:NET-04|Egress for third-party callers restricted to approved allowlist.⟧

## Secrets

- ⟦S:SECRET-01|No secrets in code, config, specs or infra definitions.⟧
- ⟦S:SECRET-02|Runtime secrets fetched from approved secret store at startup.⟧

## Logging

- ⟦S:LOG-01|Log auth failures, privilege changes, access to sensitive data.⟧

## App / ops

- ⟦S:API-01|External input validated against schema, invalid rejected.⟧
- ⟦S:API-03|Webhook payloads signed, signatures verified (in + out).⟧
- ⟦S:API-04|Error responses: no stack traces, SQL, internal hostnames.⟧
- ⟦S:API-05|Parameterized queries only.⟧
- ⟦S:OPS-01|CI scans deps and images; criticals fixed within 14 days.⟧
- ⟦S:OPS-02|Containers non-root, RO rootfs where possible.⟧

## Behavior notes

- Authorize/capture split: capture <= authorized amount, partial capture allowed once.
- Refund: up to captured amount, multiple partials ok, async ack via event.
- Idempotency: reference + merchant_id unique; repeat returns original.
- Events: payment.authorized / captured / refunded / failed on payment-events, at-least-once.
