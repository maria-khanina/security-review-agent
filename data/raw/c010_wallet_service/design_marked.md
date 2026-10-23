# wallet service: topology and notes

```
 [Mobile app]
      |  wallet + transfer requests
      v
 +---------------------+   token validation   +-----------+
 | Mobile API Gateway  |--------------------->|  Keycloak |
 +---------------------+                      +-----------+
      |  authenticated requests
      v
 +---------------------+   balances, txns   +--------------------+
 |    wallet-core      |------------------->| wallet-db (PG)     |
 +---------------------+                    +--------------------+
```

## API (as built)

- GET /v1/wallets/{walletId}: wallet + balance. Resp: id, owner_name, balance, currency.
- POST /v1/wallets/{walletId}/topups: top-up from funding source. Req: amount, funding_source_id. Resp: id, type, amount, created_at.
- POST /v1/transfers: wallet to wallet. Req: from_wallet_id, to_wallet_id, amount, note. Resp: same txn shape.
- GET /v1/wallets/{walletId}/transactions: txn list.
- PATCH /v1/wallets/{walletId}/profile: owner_name, phone_number, address.

⟦F3|The service exposes only the endpoints listed in the API section.⟧

⟦F5|All state-changing operations require an authenticated caller.⟧

## Boxes, one line each

- Gateway: single ingress, validates tokens against Keycloak, forwards to wallet-core. Mobile traffic only.
- wallet-core: balance math, transfer saga, idempotency on transfer reference.
- ⟦F4|wallet-db (PostgreSQL) stores balances, transactions and the wallet owner profile.⟧
- Keycloak: IdP for customers; realm per market.

## Auth and access

- ⟦F1|Passwords in Keycloak's legacy import table are hashed with plain SHA-256 without a per-user salt, kept that way to avoid forcing a reset.⟧

## Data

- ⟦S:CRYPTO-01|PII is encrypted at rest with AES-256.⟧
- ⟦S:CRYPTO-06|Keys live in KMS, never next to the data, rotated at least annually.⟧
- ⟦S:DATA-03|Personal data goes to third parties only under an approved DPA, only required fields.⟧
- ⟦S:DATA-04|Non-prod environments hold no real personal or card data.⟧
- ⟦F2|Backups are copied to a separate account without encryption, which keeps cross-account restore trivial.⟧

## Transport and edge

- ⟦S:CRYPTO-07|Outbound TLS connections validate certificates; verification is never off.⟧
- ⟦S:CRYPTO-05|Approved algorithms only; MD5, SHA-1, DES, 3DES and ECB are banned.⟧
- ⟦S:NET-01|wallet-db sits in private subnets, no public endpoint.⟧
- ⟦S:NET-05|A WAF with rate limiting protects the externally exposed API.⟧
- ⟦S:NET-04|Egress to third parties is restricted to an approved allowlist.⟧

## Secrets

- ⟦S:SECRET-01|No secrets in code, config, specs or infra definitions.⟧
- ⟦S:SECRET-02|At startup the service fetches its secrets from the approved secret store.⟧

## Logging

- ⟦S:LOG-01|Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.⟧

## App and ops

- ⟦S:API-01|External input is validated against a schema; invalid requests are rejected.⟧
- ⟦S:API-03|Webhook payloads are signed and signatures verified.⟧
- ⟦S:API-04|Error responses carry no stack traces, SQL or internal hostnames.⟧
- ⟦S:API-05|Queries are parameterized; no string concatenation of user input.⟧
- ⟦S:OPS-01|CI scans dependencies and images; critical vulns fixed within 14 days.⟧
- ⟦S:OPS-02|Containers run non-root, read-only root fs where possible.⟧

## Notes on behavior

Transfers are two-phase: reserve on the source wallet, credit the target, then confirm; a crash between phases is resolved by the saga on restart. A top-up is accepted as pending and flips to completed when the funding source confirms. Profile changes take effect immediately and are echoed in the response.
