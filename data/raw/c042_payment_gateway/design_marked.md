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
- ⟦S:OPS-03|Encrypted backups are checked by a restoration exercise at least twice a year.⟧
- ⟦S:LOG-02|Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.⟧
- ⟦S:AUTHZ-01|Every request for a merchant-owned payment verifies that the caller owns it or is entitled to it.⟧
- ⟦S:AUTHZ-04|Debug and administrative routes are not exposed to the internet.⟧
- ⟦S:AUTHZ-05|Production access rights are reviewed every quarter.⟧

## Notes: data

- ⟦S:CRYPTO-01|All personally identifiable information is encrypted before it lands on disk, using AES-256.⟧
- ⟦S:DATA-02|The retention period is 24 months for customer records and 90 days for delivery logs, and expired data is removed by a scheduled deletion job.⟧
- ⟦S:CRYPTO-02|The PAN is tokenized by the card token vault and only the token is kept.⟧
- ⟦S:CRYPTO-03|External traffic is served over TLS 1.2 or newer.⟧
- ⟦S:LOG-04|The central logs are readable by the platform operators, who need them to keep the service running, and by the auditors, who need them for their yearly review; all other roles are denied.⟧
- ⟦S:NET-05|External APIs must sit behind a WAF with rate limiting.⟧
- ⟦S:AUTH-02|Service-to-service calls are authenticated, either with mutual TLS between the workloads or with a signed workload identity token.⟧
- ⟦S:CRYPTO-05|We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.⟧
- ⟦S:DATA-01|The data inventory of the service lists every stored personal field with its purpose, and a field without a listed purpose is not collected.⟧
- ⟦S:SECRET-02|At startup the service fetches its secrets from the approved secret store.⟧
- ⟦S:CRYPTO-06|Encryption keys must be held in KMS, never stored with the data they protect, and rotated at least annually.⟧
- ⟦S:DATA-03|Data goes to the processor under the signed data processing agreement and only the fields it needs for the contracted task are sent: the order reference and the delivery address, because nothing else is required for delivery.⟧
- ⟦S:DATA-05|Reports and exports with personal data are available only to authorized users, stored encrypted, and deleted after 7 days.⟧

## Notes: platform

- ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧
- ⟦S:NET-01|payments-db and the Kafka brokers are in private subnets and not publicly reachable.⟧
- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧
- ⟦S:OPS-01|Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less.⟧
- ⟦S:API-01|Schema validation runs on every external input, and invalid data never reaches the business logic.⟧
- ⟦S:API-05|We use parameterized queries only, with no SQL built from user input by string concatenation.⟧
