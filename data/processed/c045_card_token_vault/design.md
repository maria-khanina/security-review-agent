# Card Token Vault: Architecture and Security Control Catalogue

Author: Rina M., Security Champion, Payments Platform
Review: Security Architecture
Revision: 6 (revision 5 called the service "vault-svc"; the old name is retired but remains in two runbooks)

## 1. Summary

The card token vault tokenizes primary account numbers (PANs) for the payment services and is the only component in the estate that stores them. This document describes the architecture and catalogues the controls that apply to the Vault. Reviewers should read the catalogue (section 5) first, because the Vault defines the boundary of the platform's PCI scope.

## 2. Architecture

The Vault runs in a dedicated private subnet, referred to as the vault private subnet. It has four parts:

- **tokenization-service**: exposes tokenize (PAN to token) and detokenize (token to PAN) to payment services.
- **vault-db (PostgreSQL)**: stores card records in encrypted form together with the token mapping.
- **Vault and KMS**: the secret store and the key service used by the tokenization-service.
- **The vault private subnet**: the network boundary around the service and its database.

Payment services call the tokenization-service. The tokenization-service reads and writes card records in vault-db and asks Vault and KMS for data encryption keys. The infrastructure is declared in Terraform: the KMS key `vault_key`, the database `vault_db`, the security group `vault_db_sg`, the log group `vault_audit`, the backup vault `vault_backups` and the IAM policy `vault_service_policy`.

## 3. Data flows

Tokenize: a payment service submits a PAN; the service encrypts it, stores it, and returns a token. The token is random and has no mathematical relation to the PAN. Detokenize: a payment service submits a token and a purpose code; the service checks the purpose, decrypts the card record and returns the PAN. Each detokenize call produces an audit record with the caller, the purpose and the token.

## 4. Roles

The Vault defines three roles: operator (deploys and restarts), auditor (reads the audit trail) and key custodian (starts key rotation). Service accounts of the payment services hold only the tokenize and detokenize permissions that their purpose codes allow.

## 5. Control catalogue

Control identifiers (V-1 and so on) match the compliance spreadsheet (link TBD; the older spreadsheet under the previous team name is stale and may not open).

### 5.1 Identity and access

- V-1: Calls from payment services to the tokenization-service are authenticated with mutual TLS or signed workload identity tokens.
- V-2: Staff roles are limited to what each job needs, and every service defines its own roles.
- V-3: Every three months the system owners review who has access to production and remove what is no longer needed.

Nothing administrative or meant for debugging can be called from outside our network.

### 5.2 Cardholder data

- V-4: The PAN is tokenized by the card token vault and only the token is kept.
- V-5: The approved algorithm list is followed, and MD5, SHA-1, DES, 3DES and ECB mode are prohibited in this service.

At startup the service fetches its secrets from the approved secret store.

### 5.3 Secrets

- V-6: Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.

Personal data goes to third parties only under an approved data processing agreement, and only the required fields are sent.

### 5.4 Network

- V-8: The database is exposed with a public endpoint to ease analyst access. Analysts connect with their own read-only accounts from the office network. This entry replaces the older V-8, which said that no analyst access to the Vault database exists.

### 5.5 Logging

- V-9: Authentication failures, privilege changes and access to sensitive data are logged.

### 5.6 Application security

- V-12: We use parameterized queries only, with no SQL built from user input by string concatenation.

Every engineer has read access to the production logs of the vault.

Schema validation runs on every external input, and invalid data never reaches the business logic.

### 5.7 Operations

## 6. Capacity and resilience

The expected peak is a few hundred tokenize calls per second at month end, with detokenize at roughly half that rate. The service is stateless and scales horizontally behind an internal load balancer; the database runs as a primary with a standby in a second availability zone. Deployments are rolling. A canary instance receives a small share of traffic for fifteen minutes before the rest is updated, and rollback is automatic when the error rate crosses a threshold.

The recovery objective for a regional failure is four hours. A restore into the standby region is described in the runbook, and the payment services are switched over by changing the Vault endpoint in their configuration. A quarterly game day exercises this procedure. The earlier four-hour figure appears in revision 5 as two hours; four hours is correct.

## 7. Key management lifecycle

Data encryption keys are generated by Vault and KMS and are never exposed to operators. A key rotation worker rotates keys on a schedule, re-wraps the stored keys and records the rotation in the audit trail. Detokenization continues to work during rotation because old key versions stay available until all records are re-wrapped.

## 8. Change management

Changes to the Vault follow the standard change process, with two additional rules: every change is reviewed by a member of the payments security team, and every change that touches the key hierarchy needs approval from the key custodian role. Emergency changes are allowed but are reviewed within two working days.

## 9. Open items

- The status column of the catalogue is kept in the spreadsheet and not in this document; reviewers should consult it (link TBD).
- The purpose-code list for detokenize is being reviewed with Compliance.
- Reference to the original design from revision 1 lives in the archived wiki space and may not open.
