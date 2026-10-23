# PGW topology

```
 [Merchant backend]
        |   payment request (card token)
        v
 +--------------------------+
 |  Payments Edge Gateway   |
 +--------------------------+
        |   validated payment request
        v
 +--------------------------+     authorization request     +--------------------+
 |      payments-core       |------------------------------>| Acquirer connector |
 +--------------------------+                               +--------------------+
     |              |
     | records      | status events
     v              v
 +----------------+  +-------------------------+
 | payments-db(PG)|  | payment-events (Kafka)  |
 +----------------+  +-------------------------+
```

## API

- POST /v1/payments: create. Req: amount, currency, card_token, merchant_id, reference. Resp: id, status, amount, currency, last4, merchant_id.
- GET /v1/payments/{paymentId}: fetch one.
- POST /v1/payments/{paymentId}/capture: capture. Req: amount.
- POST /v1/payments/{paymentId}/refunds: refund. Req: amount, reason. Resp: id, status, amount.
- GET /v1/payments: list.

## Captions

- Edge: single public ingress. All merchant traffic enters here, nothing else is exposed.
- payments-core: owns payment state (created, authorized, captured, refunded, failed). Idempotent on reference + merchant_id.
- Acquirer connector: adapter per acquirer, one outbound path.
- payment-events: state changes, at-least-once, consumers dedupe on payment id.

## Notes: access

- Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.
- Every request for a merchant-owned payment verifies that the caller owns it or is entitled to it.
- Administrative and debug endpoints are not reachable from the public internet.
- Access rights to production systems are reviewed at least quarterly.

## Notes: data

- Personally identifiable information is encrypted at rest with AES-256.
- Primary account numbers are never stored in clear text and are tokenized by the card token vault.
- All external traffic uses TLS 1.2 or higher.
- Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- Only the personal data needed for payment processing is collected and stored.
- Personal data goes to third parties only under an approved data processing agreement, and only the fields required.
- Reports and exports with personal data require authorization, are encrypted in storage and expire.

## Notes: platform

- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- payments-db and the Kafka brokers are in private subnets and not publicly reachable.
- Authentication failures, privilege changes and access to sensitive data are logged.
- External inputs are validated against a schema and rejected if invalid.
- Database queries are parameterized; concatenating user input into queries is prohibited.
