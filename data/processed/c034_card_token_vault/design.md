# Card Token Vault: Design and Compliance Statement

Document owner: Payments Compliance
Version: 2.0 (supersedes 1.x; see the archive for earlier versions, link TBD)

## 1. Purpose and Scope

This document describes the design of the Card Token Vault ("the Vault") and states, for each applicable requirement of the Meridian Pay Information Security Policy, how the Vault satisfies it. The Vault is the single component of the platform that processes primary account numbers (PANs). All other services handle tokens only. The document covers the production environment and the environments that support it.

## 2. System Description

The Vault consists of the following components, all deployed in the vault private subnet:

- tokenization-service, which exposes two operations to payment services: tokenization of a PAN and detokenization of a token;
- vault-db (PostgreSQL), which stores card records in encrypted form;
- Vault and KMS, which provide runtime secrets and data encryption keys;
- the network configuration of the vault private subnet.

The infrastructure is declared in Terraform and consists of the KMS key `vault_key`, the database instance `vault_db`, the security group `vault_db_sg`, the log group `vault_audit`, the backup vault `vault_backups` and the IAM policy `vault_service_policy`.

Payment services send PANs to the tokenization-service and receive tokens. To charge a card, they send a token and receive the PAN in the reply. The tokenization-service writes the encrypted card data to vault-db and requests data encryption keys from Vault and KMS. The tokenization-service writes request logs for every tokenize and detokenize call. The tokenization-service also writes an audit record for every tokenize and detokenize operation to the log group.

## 3. Identity and Access Control

3.1 In accordance with policy, calls from payment services to the tokenization-service are authenticated with mutual TLS or signed workload identity tokens.

3.2 Where workload identity tokens are used, access tokens expire within 15 minutes, and refresh tokens are rotated on use.

3.3 The Vault defines the roles operator, auditor and key custodian.

## 4. Cardholder Data Protection

4.1 The PAN is tokenized by the card token vault and only the token is kept. Tokens are random values with no mathematical relationship to the PAN.

4.2 Encryption keys are held in KMS, are never stored with the data they protect, and are rotated at least annually.

4.3 Traffic between services, and between services and data stores or brokers, is encrypted in transit.

4.4 Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.

4.5 The Vault validates TLS certificates on every TLS connection it makes and never disables verification.

4.6 Non-production environments do not contain real personal or card data; test PANs from the card network test ranges are used instead.

## 5. Secrets Management

5.1 Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.

5.2 Runtime secrets are fetched from the approved secret store when the Vault starts.

## 6. Network

6.1 vault-db and the message brokers are deployed in private subnets and are not publicly reachable.

6.2 Outbound traffic from services that call third parties is restricted to an approved allowlist.

## 7. Monitoring

7.1 Authentication failures, privilege changes and access to sensitive data are logged. The auditor role has read access to the log group.

## 8. Application Security

8.1 Callback payloads for token lifecycle events, both outbound and inbound, are signed, and the signatures are verified.

8.2 We use parameterized queries only, with no SQL built from user input by string concatenation.

## 9. Operations

9.1 The continuous integration pipeline scans dependencies and container images, and critical vulnerabilities are fixed within 14 days.

9.2 Containers run as a non-root user, with a read-only root filesystem where possible.

## 10. Operational Characteristics

The expected peak load is a few hundred tokenize calls per second at month end, with detokenize at roughly half that rate. The Vault is deployed as an active service with a standby database in a second availability zone. Deployments are rolling; one instance is replaced at a time and the health check must pass before the next is touched. The recovery objective for a regional failure is four hours and is exercised in a quarterly game day.

Detokenization requires a purpose code. The permitted purposes are charge, refund, chargeback and reconciliation. A request with an unknown purpose code is rejected before any data is read. The purpose list is reviewed with Compliance once a year.

## 11. Outstanding Items

- Date of the next key ceremony: TBD with Security.
- Final text of the operator runbook: TBD; see the draft in the wiki space "Vault Ops" (the older space under the previous team name is stale).
