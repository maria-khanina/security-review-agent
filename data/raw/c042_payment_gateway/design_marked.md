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

- ⟦S:AUTH-01|No external endpoint serves anonymous traffic; callers present an OAuth2 token or a TLS client certificate.⟧
- ⟦S:AUTHZ-01|Every request for a merchant-owned payment verifies that the caller owns it or is entitled to it.⟧
- ⟦S:AUTHZ-04|Debug and administrative routes are not exposed to the internet.⟧
- ⟦S:AUTHZ-05|Production access rights are reviewed every quarter.⟧

## Notes: data

- ⟦S:CRYPTO-01|All personally identifiable information is encrypted before it lands on disk, using AES-256.⟧
- ⟦S:CRYPTO-02|The PAN is tokenized by the card token vault and only the token is kept.⟧
- ⟦S:CRYPTO-03|External traffic is served over TLS 1.2 or newer.⟧
- ⟦S:CRYPTO-05|We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.⟧
- ⟦S:DATA-01|Only the personal data needed for payment processing is collected and stored.⟧
- ⟦S:DATA-03|Personal data goes to third parties only under an approved data processing agreement, and only the fields required.⟧
- ⟦S:DATA-05|Reports and exports with personal data require authorization, are encrypted in storage and expire.⟧

## Notes: platform

- ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧
- ⟦S:NET-01|payments-db and the Kafka brokers are in private subnets and not publicly reachable.⟧
- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧
- ⟦S:API-01|Schema validation runs on every external input, and invalid data never reaches the business logic.⟧
- ⟦S:API-05|We use parameterized queries only, with no SQL built from user input by string concatenation.⟧
