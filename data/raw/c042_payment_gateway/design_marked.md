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

- ⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧
- ⟦S:AUTHZ-01|Every request for a merchant-owned payment verifies that the caller owns it or is entitled to it.⟧
- ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧
- ⟦S:AUTHZ-05|Access rights to production systems are reviewed at least quarterly.⟧

## Notes: data

- ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧
- ⟦S:CRYPTO-02|Primary account numbers are never stored in clear text and are tokenized by the card token vault.⟧
- ⟦S:CRYPTO-03|All external traffic uses TLS 1.2 or higher.⟧
- ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
- ⟦S:DATA-01|Only the personal data needed for payment processing is collected and stored.⟧
- ⟦S:DATA-03|Personal data goes to third parties only under an approved data processing agreement, and only the fields required.⟧
- ⟦S:DATA-05|Reports and exports with personal data require authorization, are encrypted in storage and expire.⟧

## Notes: platform

- ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧
- ⟦S:NET-01|payments-db and the Kafka brokers are in private subnets and not publicly reachable.⟧
- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧
- ⟦S:API-01|External inputs are validated against a schema and rejected if invalid.⟧
- ⟦S:API-05|Database queries are parameterized; concatenating user input into queries is prohibited.⟧
