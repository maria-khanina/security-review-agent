# Card Token Vault: stories and design

Epic: VAULT-40 (Vault v2 platform)
Status: Ready for development
Related: VAULT-31 (v1 retirement, link may not open)

## Overview

The card token vault tokenizes primary account numbers (PANs) for the payment services. It runs in the vault private subnet and consists of the tokenization-service, vault-db (PostgreSQL) and Vault and KMS. The infrastructure is declared in Terraform: `vault_key` (KMS), `vault_db` (RDS), `vault_db_sg` (security group), `vault_audit` (log group), `vault_backups` (backup vault) and `vault_service_policy` (IAM).

## Stories

### VAULT-41: Tokenize

As a payment service, I want to send a PAN and receive a token so that I never have to hold the PAN.

Acceptance criteria:
- The tokenization-service accepts a PAN, validates its format and returns a token.
- The same PAN yields the same token for the same merchant.
- Tokens are random and have no mathematical relation to the PAN.

### VAULT-42: Detokenize

As a payment service, I want to send a token with a purpose code and receive the PAN so that I can call the acquirer.

Acceptance criteria:
- A request with an unknown purpose code is rejected before any data is read.
- Permitted purposes are charge, refund, chargeback and reconciliation.
- Every call produces an audit record with caller, purpose and token.

### VAULT-43: Rotate keys

As a key custodian, I want to rotate data encryption keys so that exposure is bounded.

Acceptance criteria:
- A worker re-wraps stored keys on a schedule.
- Detokenization keeps working during rotation.
- The rotation is recorded in the audit trail.

### VAULT-44: Recover from a regional failure

As the on-call engineer, I want to restore the vault in the standby region so that payments can resume.

Acceptance criteria:
- The restore procedure is in the runbook (TBD: link the new runbook).
- The recovery objective is four hours.
- The procedure is exercised in a quarterly game day.

## Non-functional requirements

Listed once for the epic (TBD: copy into each story as acceptance criteria).

| ID | Area | Requirement |
|---|---|---|
| NFR-1 | Service authentication | ⟦S:AUTH-02|Calls from payment services to the tokenization-service are authenticated with mutual TLS or signed workload identity tokens.⟧ |
| NFR-2 | Roles | ⟦S:AUTHZ-02|Internal users receive only the roles required for their job, and roles are defined per service.⟧ |
| NFR-3 | Access review | ⟦S:AUTHZ-05|Every three months the system owners review who has access to production and remove what is no longer needed.⟧ |
| NFR-4 | Cardholder data | ⟦S:CRYPTO-02|Primary account numbers are never stored in clear text and are tokenized by the card token vault.⟧ |
| NFR-5 | Algorithms | ⟦S:CRYPTO-05|The approved algorithm list is followed, and MD5, SHA-1, DES, 3DES and ECB mode are prohibited in this service.⟧ |
| NFR-6 | Secrets in artifacts | ⟦S:SECRET-01|Source, config, specs and infrastructure definitions contain no secrets.⟧ |
| NFR-8 | Network | ⟦S:NET-01|vault-db and the message brokers sit in private subnets and are not publicly reachable.⟧ |
| NFR-9 | Security logging | ⟦S:LOG-01|Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.⟧ |
| NFR-12 | Queries | ⟦S:API-05|All queries use bound parameters instead of string concatenation.⟧ |

⟦S:AUTHZ-04|The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.⟧
⟦S:DATA-05|Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.⟧
⟦S:DATA-03|Third parties receive only the fields they need, and only if an approved data processing agreement covers them.⟧
⟦S:API-01|All external input is validated against a schema, and invalid requests are rejected.⟧
⟦S:DATA-01|The service collects and stores only the personal data it needs for its purpose.⟧

## Design notes

The tokenization-service is stateless and scales horizontally behind an internal load balancer. The database runs as a primary with a standby in a second availability zone. Deployments are rolling; a canary instance receives a small share of the traffic for fifteen minutes before the rest is updated, and rollback is automatic when the error rate crosses an agreed threshold. The expected peak is a few hundred tokenize calls per second at month end, with detokenize at about half that rate.

## Definition of done

- Acceptance criteria demonstrated in staging.
- Runbook updated.
- Game day scheduled for the quarter after release.
