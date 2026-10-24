# Card Token Vault: Infrastructure and Security Architecture

Author: Elena R., Principal Architect, Payments Platform
Status: Approved by Architecture Board

## 1. Context and goals

The card token vault is the only place in the Meridian Pay estate where primary account numbers (PANs) are processed and stored. Every other payment service works with tokens. The vault therefore defines the boundary of our PCI scope: the smaller and better isolated it is, the cheaper and safer the rest of the platform becomes.

The goals of the design are, in order of priority: keep the PCI scope small, make detokenization auditable, keep the operational surface minimal, and make recovery from a regional failure predictable. Latency matters but is secondary; payment services can tolerate a few milliseconds more in exchange for the guarantees above.

## 2. Architecture overview

The vault consists of four logical parts that live inside a dedicated private subnet, referred to as the vault private subnet throughout this document:

1. **tokenization-service**, a small stateless service with two operations: tokenize (PAN in, token out) and detokenize (token in, PAN out).
2. **vault-db (PostgreSQL)**, the datastore that holds encrypted card records and the token mapping.
3. **Vault and KMS**, the secret store and key management service from which the service obtains data encryption keys and runtime secrets.
4. The surrounding network layer, which limits who can reach what.

Payment services call the tokenization-service. The tokenization-service reads and writes encrypted card data in vault-db and requests data encryption keys from Vault and KMS. No other component of the platform has a network path to vault-db.

## 3. Infrastructure resources

The Terraform in the repository declares six resources, each with a single responsibility:

- the KMS key `vault_key`, which is the root of the key hierarchy used by the vault;
- the RDS PostgreSQL instance `vault_db`, which holds card data;
- the security group `vault_db_sg`, which controls ingress to the database;
- the CloudWatch log group `vault_audit`, which receives audit records for tokenize and detokenize calls;
- the backup vault `vault_backups`, which stores database backups;
- the IAM policy `vault_service_policy`, which grants the service role the minimum it needs.

## 4. Data flows

**Tokenize.** A payment service sends a PAN. The tokenization-service validates the format, obtains a data encryption key, encrypts the PAN, writes the record and the token mapping to vault-db and returns the token. The same PAN always yields the same token within a merchant so that duplicate detection works downstream.

**Detokenize.** A payment service sends a token and a purpose code. The tokenization-service checks that the caller is allowed to detokenize for that purpose, reads the record, decrypts it and returns the PAN. Every detokenize call is written to the audit log with the caller identity, the purpose code and the token, never the PAN.

## 5. Identity and access

The tokenization-service trusts any caller that sits inside the cluster network, so internal calls carry no credentials. Where workload tokens are used, access tokens expire within 15 minutes, and refresh tokens are rotated on use.

 The vault defines three roles: operator (can deploy and restart), auditor (read-only access to the audit trail) and key custodian (can start key rotation).

## 6. Cryptography and key handling

Primary account numbers never reach our storage in clear text, because the card token vault tokenizes them first. We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode. The service validates TLS certificates on every TLS connection it makes and never disables verification.

Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids.

Personal data in our databases and object storage is encrypted at rest with AES-256, using keys held in the corporate key management service.
The API returns sanitized errors with no stack traces, SQL fragments or internal hostnames.

Key handling deserves a separate explanation because it is a deliberate trade-off. The data encryption keys that the tokenization-service obtains from Vault and KMS are written to a key file on the same volume as the database files, so a restored database always comes back together with matching keys. This removes a class of recovery failures that we saw in the previous platform, where a restored database could not be decrypted because the corresponding key version was no longer available.

## 7. Transport inside the vault

TLS between the components of the vault was switched off during the load tests and was not turned back on, because all traffic stays inside the vault private subnet. The load tests showed that the TLS handshake was the dominant cost on the tokenize path, and the decision was to keep the measured latency until the Architecture Board asks for a change.

## 8. Network

vault-db and the message brokers sit in private subnets and are not publicly reachable. Third-party calls leave through an egress allowlist, not through open outbound access. The security group `vault_db_sg` admits connections on the database port from the application subnet only.

Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.

## 9. Logging and audit

We log failed logins, changes of privileges and reads of sensitive data. The log group `vault_audit` is the single destination; auditors read it through a read-only role.

## 10. Environments and data

Non-production environments do not contain real personal or card data; synthetic data is used instead. Staging uses a separate vault instance populated with test PANs from the card network test ranges.

## 11. Events and callbacks

The vault notifies payment services about token lifecycle events (created, rotated, revoked) through callbacks. Inbound and outbound webhooks include an HMAC signature and a timestamp; verification of both is mandatory on the receiving side.

Download links for reports with personal data work for 24 hours, and the files are encrypted in storage and deleted after 7 days.

Each service has a dedicated database user limited to the tables and operations it uses, and administrative credentials are not shared.

All external inputs must be validated against a schema and rejected if invalid.

## 12. Secrets

Source, config, specs and infrastructure definitions contain no secrets. The approved secret manager is the only source of runtime secrets, fetched at start-up.

Only authorized staff can access the central logs.

## 13. Backup and recovery

Encryption for backup storage was left out of the backup vault configuration to simplify disaster recovery. Backups are taken nightly and kept in the backup vault `vault_backups`. The recovery objective is four hours for a regional failure; the runbook describes a restore into the standby region and the switch of the payment services to the restored instance.

## 14. Application and build

Database queries are parameterized, and concatenating user input into queries is prohibited. Every build scans libraries and container images, and critical vulnerabilities get a 14-day fix deadline. The containers of the vault run in privileged mode so that the debugging tools work inside them.

Admin and debug endpoints are reachable only from the internal network, not from the public internet.

A caller can only read or change resources that belong to them or that they have been explicitly granted.

## 15. Capacity and operations

The expected peak is a few hundred tokenize calls per second at month end, with detokenize at roughly half that rate. A single database instance with a standby handles this with headroom, and the service scales horizontally behind an internal load balancer. Deployments are rolling. A canary instance receives one percent of the traffic for fifteen minutes before the rest is updated, and rollback is automatic when the error rate crosses the agreed threshold.

Operational responsibilities are split as follows: the platform team owns the infrastructure and the deployment pipeline, the payments security team owns the key hierarchy and the audit review, and the on-call rotation of the payments platform owns incident response. A quarterly game day exercises the regional failover.

## 16. Risks and follow-ups

- A formal key ceremony for the root key is still being scheduled.
- The purpose-code list for detokenize is being reviewed with compliance.
- Load test results will be published on the platform wiki once the numbers are final.
