# Card Token Vault: Platform Vision and Design

Owner: Payments Platform
Status: Approved, build in progress

## 1. Vision

Every payment product we ship needs to handle cards, and every one of them should be able to do so without ever holding a card number. The Card Token Vault is the platform capability that makes this possible. Payment services hand it a card number and receive a token; when they need to charge, they hand the token back. The vault keeps the sensitive part of the world small, auditable and well guarded, so that the rest of the platform can move fast.

The vault is designed to be the foundation for the next two years of payments work: wallet top-ups from cards, recurring payments, one-click checkout and card-on-file for merchants. Each of these reuses the same two operations, tokenize and detokenize, and each of them benefits automatically from every control described below.

## 2. Architecture

The vault runs in its own private subnet, referred to as the vault private subnet. It has four parts: the tokenization-service, which exposes tokenize and detokenize; vault-db (PostgreSQL); Vault and KMS, which supply data keys and runtime secrets; and the network around them.

⟦F1|vault-db (PostgreSQL) is the main datastore of the vault and runs as a primary with a standby in a second availability zone.⟧

The infrastructure is declared in Terraform: the KMS key `vault_key`, the database `vault_db`, the security group `vault_db_sg`, the log group `vault_audit`, the backup vault `vault_backups` and the IAM policy `vault_service_policy`.

## 3. Capabilities

**Tokenize.** A payment service sends a card number and receives a token. The same card yields the same token for the same merchant, so duplicates are easy to detect downstream.

**Detokenize.** A payment service sends a token with a purpose code and receives the card number for the acquirer call. The purpose code is checked before anything is read, and every call produces an audit record.

**Key rotation.** A worker rotates data encryption keys on a schedule. Detokenization continues to work during rotation because old key versions remain available until all records have been re-wrapped.

## 4. Security controls

- ⟦S:AUTH-02|Calls from payment services to the tokenization-service are authenticated with mutual TLS or signed workload identity tokens.⟧
- ⟦S:AUTHZ-02|Staff roles are limited to what each job needs, and every service defines its own roles.⟧
- ⟦S:SECRET-02|Runtime secrets are read from the secret store when the service starts.⟧
- ⟦S:CRYPTO-04|Traffic between services and to data stores must be encrypted in transit.⟧
- ⟦S:AUTHZ-05|A quarterly access review covers all production systems.⟧
- ⟦S:LOG-04|The log platform is access-controlled, and only authorized staff can read the logs.⟧
- ⟦S:CRYPTO-05|Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.⟧
- Data at rest is encrypted with KMS-managed keys.
- ⟦S:SECRET-01|No secrets are kept in source code, config files, API specs or infrastructure definitions.⟧
- ⟦S:DATA-02|Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.⟧
- ⟦S:NET-01|vault-db and the message brokers sit in private subnets and are not publicly reachable.⟧
- ⟦S:AUTHZ-01|Ownership is verified on every access to customer-owned data, not only at login.⟧
- ⟦S:API-01|All external inputs must be validated against a schema and rejected if invalid.⟧
- ⟦S:DATA-05|Each export file is encrypted at rest, readable only by the authorized requester, and removed automatically after 72 hours.⟧
- ⟦S:CRYPTO-06|Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year.⟧
- ⟦S:OPS-03|Encrypted backups are checked by a restoration exercise at least twice a year.⟧
- ⟦S:DATA-03|Third parties receive only the fields they need, and only if an approved data processing agreement covers them.⟧
- ⟦S:LOG-02|Log lines are kept free of secrets, card numbers and personal details, and identifiers are opaque.⟧

## 5. Logging and audit

⟦F2|Access to customer records is not recorded anywhere.⟧ The audit trail covers calls to the vault only.

⟦S:AUTH-03|Access tokens live for at most 15 minutes, and every refresh token is replaced when it is used.⟧

## 6. Build and operations

⟦F4|A raw SQL fragment from the query string is appended to the report query.⟧

The service is stateless and scales horizontally behind an internal load balancer; the database primary is the single writer. The expected peak is a few hundred tokenize calls per second at month end, with detokenize at about half that rate. Deployments are rolling, and a canary instance receives a small share of the traffic before the rest is updated.

## 7. Roadmap

The vault is built in three increments. Increment one delivers tokenize and detokenize with the controls above. Increment two adds merchant-scoped tokens so that a token from one merchant cannot be used by another. Increment three adds network tokens for the card schemes and automatic card updates. Each increment is released behind a flag and is rolled out first to internal test merchants.

The recovery objective for a regional failure is four hours and will be exercised in a quarterly game day once increment two is live.

## 8. Open items

- The final list of purpose codes for detokenize is being agreed with Compliance.
- The date of the key ceremony for the root key is not yet fixed.
