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
- ⟦S:AUTHZ-05|A quarterly access review covers all production systems.⟧
- ⟦S:CRYPTO-05|Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.⟧
- ⟦F2|Data at rest is encrypted with KMS-managed keys.⟧
- ⟦S:SECRET-01|No secrets are kept in source code, config files, API specs or infrastructure definitions.⟧
- ⟦S:NET-01|vault-db and the message brokers sit in private subnets and are not publicly reachable.⟧

## 5. Logging and audit

⟦F3|Access to customer records is not recorded anywhere.⟧ The audit trail covers calls to the vault only.

## 6. Build and operations

⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧

The service is stateless and scales horizontally behind an internal load balancer; the database primary is the single writer. The expected peak is a few hundred tokenize calls per second at month end, with detokenize at about half that rate. Deployments are rolling, and a canary instance receives a small share of the traffic before the rest is updated.

## 7. Roadmap

The vault is built in three increments. Increment one delivers tokenize and detokenize with the controls above. Increment two adds merchant-scoped tokens so that a token from one merchant cannot be used by another. Increment three adds network tokens for the card schemes and automatic card updates. Each increment is released behind a flag and is rolled out first to internal test merchants.

The recovery objective for a regional failure is four hours and will be exercised in a quarterly game day once increment two is live.

## 8. Open items

- The final list of purpose codes for detokenize is being agreed with Compliance.
- The date of the key ceremony for the root key is not yet fixed.
