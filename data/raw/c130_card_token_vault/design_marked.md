# Card Token Vault: Design Overview

Maintainers: payments platform team
Revision history: 0.2 (tokenizer), 0.5 (vault), 0.8 (this text, merged with the "PAN Safe" notes; some parts are older)

## 1. What the vault does

The Card Token Vault tokenizes primary account numbers. Payment services send a card number and receive a token; later they send the token and, if they are allowed, receive the number back. All card numbers of Meridian Pay live in this one place so that the rest of the platform can stay out of the heaviest part of the PCI scope. The vault is internal. It is called only by other platform services and no customer or merchant calls it. In older documents it is called "PAN Safe", "the tokenizer" or "the vault"; in this text these names mean the same system until the old pages are retired.

## 2. Background

The first tokenizer was built in 2020 as a library inside the payment gateway. When the wallet service and the refund flow needed tokens too, copies of the library appeared in three services and the card numbers were stored in three databases. The vault consolidates this: one service, one database, one audit trail. The migration of the three old stores is described in the "PAN Safe" notes (link no longer available) and is not repeated here.

## 3. Components

- **tokenization-service** is a stateless service that implements tokenize and detokenize. It runs as three replicas in the vault private subnet.
- **vault-db (PostgreSQL)** holds the encrypted card data and the mapping between tokens and card numbers. It runs as a primary with a standby in a second availability zone.
- **Vault and KMS** provide the data encryption keys. ⟦F2|tokenization-service asks Vault and KMS for a data encryption key when it starts and again when a key must be replaced.⟧
- **vault private subnet** is the network segment that contains all of the above.

Terraform creates `vault_key`, `vault_db`, `vault_db_sg`, `vault_audit`, `vault_backups` and `vault_service_policy`.

## 4. Behavior

Tokenize: the caller sends a card number; the service encrypts it with a data encryption key, stores it with a random token and returns the token. The same number always yields the same token for the same merchant so that merchants can recognize repeat customers without seeing the number. Detokenize: the caller sends a token and receives the number only if the caller is on the list of services that may detokenize. The list is short: the acquirer connector and the refund flow.

## 5. Authentication, version note

The calling services authenticate with the scheme described in the "PAN Safe" notes, which uses a shared key per calling service. The vault design of version 0.5 moved to signed workload identity tokens. It is not clear to the author of this merged text which of the two is currently in force for each caller, because the callers are migrating one by one and the old section was kept for reference. This is a known gap.

## 6. Control statements

6.1 Identity. ⟦S:AUTH-02|Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.⟧ ⟦S:AUTH-03|Access tokens expire within 15 minutes, and refresh tokens are rotated on use.⟧

6.2 Card data and cryptography. ⟦S:CRYPTO-02|We do not keep primary account numbers: the card token vault tokenizes them and we store the token.⟧ ⟦S:CRYPTO-04|Traffic between services, and from services to data stores, is encrypted in transit.⟧ ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧ ⟦S:CRYPTO-06|Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.⟧

6.3 Certificates. ⟦F1|Hostname verification is disabled on the connection from tokenization-service to vault-db, because the certificate of the database still carries the name of the old host.⟧

6.4 Secrets and network. ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ ⟦S:SECRET-02|On boot, the service pulls its credentials from the approved secret store.⟧ ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧ ⟦S:NET-04|The service can reach only allow-listed third-party hosts, and all other outbound traffic is blocked.⟧

⟦S:DATA-05|Reports and exports with personal data are available only to authorized users, stored encrypted, and deleted after 7 days.⟧

⟦S:LOG-04|Access to centralized logs must be limited to authorized staff.⟧

⟦S:DATA-03|Third parties receive only the fields they need, and only if an approved data processing agreement covers them.⟧

⟦S:CRYPTO-01|Databases and buckets that hold personal data use AES-256 encryption at rest, and the keys are managed in the corporate key management service.⟧
⟦S:DATA-02|Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.⟧

⟦S:AUTHZ-04|The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.⟧

⟦S:AUTHZ-01|The service compares the authenticated caller with the owner of the requested resource and rejects the request if they do not match and no entitlement exists.⟧
⟦S:AUTHZ-03|The service connects to its database with its own account, which has only the grants it needs.⟧

6.5 Logging and data. ⟦S:LOG-01|The audit trail includes authentication failures, privilege changes and sensitive-data access.⟧ ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧

6.6 Application and delivery. ⟦S:API-03|Inbound and outbound webhooks include an HMAC signature and a timestamp; verification of both is mandatory on the receiving side.⟧ ⟦S:API-05|User input reaches the database only as query parameters, never as part of the query text.⟧ ⟦S:OPS-01|Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less.⟧ ⟦S:OPS-02|No container runs as root, and the root filesystem is read-only wherever possible.⟧

⟦S:LOG-02|Log lines are kept free of secrets, card numbers and personal details, and identifiers are opaque.⟧

6.7 Backups. Backups of the vault database are encrypted.

## 7. Failure handling

If vault-db is unreachable, tokenize and detokenize return an error and nothing is cached. If the standby takes over, the replicas reconnect on their next retry, which happens within seconds. If Vault and KMS is unreachable at start, the replica does not become ready; replicas that are already running continue with the key in memory until it must be replaced. The audit log group records every detokenize call with the caller, the token and the time, but never the card number.

## 8. Capacity

The peak is around six hundred tokenize calls a second at sale events and the average is below fifty. Detokenize calls are about one tenth of tokenize calls. The database is sized for ten times the peak. A restart of one replica takes about forty seconds and does not interrupt callers because the other replicas serve the requests.

## 9. Migration

The three old stores are migrated one at a time. A store is considered done when no card numbers are left in it and its service calls the vault for every operation. During the migration both the old library and the vault accept tokens; the vault issues new tokens for numbers it has not seen. After the last store is done the library is removed from the gateway. See the "PAN Safe" runbook for the migration steps (link not valid) and the "Store inventory" sheet for the list of tables (link not valid).

## 10. Open items

The final retention of the audit log depends on the compliance team. The list of services that may detokenize is kept in a configuration file and should move to a managed list (TBD, owner: platform team). The naming of callers (service name versus team name) is not unified; the vault accepts both for now.
