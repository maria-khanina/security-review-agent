# Card Token Vault Design

Assembled from: the original PCI vault design (2020), the "tokenizer service" proposal (2021) and the migration notes for the new landing zone (2023). Passages from older documents keep their names; section 9 maps old names to current ones.

## 1. Background

The vault (called the PCI store in 2020, the tokenizer in the proposal, and the card token vault today) is the only component of the platform that handles primary account numbers (PANs). The 2020 text described a single service with its own database on a dedicated host. The current design runs in a private subnet of the new landing zone and uses managed services for the database and the keys.

## 2. Components

- **tokenization-service** (2020: pci-api; proposal: tokenizer): exposes tokenize and detokenize.
- **vault-db (PostgreSQL)** (2020: the PCI schema on host pcidb01): the datastore.
- **Vault and KMS** (2020: a file-based key store; proposal: hsm-gateway): key and secret service.
- **vault private subnet** (2020: the PCI VLAN).

## 3. Data flows

Payment services send a PAN to the tokenization-service and receive a token. To charge a card they send the token and receive the PAN. The tokenization-service stores encrypted card data in vault-db and asks Vault and KMS for data encryption keys. The 2020 text described a nightly export of tokens to the reporting database; that export was removed in 2022 and nothing reads tokens from the reporting side any more.

## 4. Infrastructure

The infrastructure is declared in Terraform in the repository. It contains six resources: the KMS key `vault_key`, the database `vault_db`, the security group `vault_db_sg`, the log group `vault_audit`, the backup vault `vault_backups` and the IAM policy `vault_service_policy`. The 2020 text described the same elements as hand-built VMs; none of them exist any more.

## 5. Security

This section replaces the 2020 and 2021 security sections. The 2020 text relied on host firewalls and a shared service password; neither applies today.

- Card numbers are never stored in clear text; they are replaced by tokens from the card token vault.
- We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.
- The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.
- Service-to-service calls are authenticated, either with mutual TLS between the workloads or with a signed workload identity token.
- Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.
- The retention period is 24 months for customer records and 90 days for delivery logs, and expired data is removed by a scheduled deletion job.
- At startup the service fetches its secrets from the approved secret store.
- We log failed logins, changes of privileges and reads of sensitive data.
- Containers must run as a non-root user with a read-only root filesystem where possible.
- Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.
- Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids.
- Connections to the database and between internal services use TLS.
- Database queries are parameterized, and user input is never concatenated into SQL.
- Every build scans libraries and container images, and critical vulnerabilities get a 14-day fix deadline.
- The application never uses a shared administrative database login; it has a dedicated, minimally privileged account.
- All external inputs must be validated against a schema and rejected if invalid.
- The databases and object stores that hold PII use AES-256 encryption at rest.
- No personal data leaves for a third party without an approved DPA, and the payload is limited to the required fields.

## 6. Deployment

The tokenization-service runs as three replicas behind an internal load balancer. The 2020 text said two replicas on separate hosts, and the proposal suggested a pool of workers; the current deployment is three identical replicas. Rolling updates replace one replica at a time. A canary replica receives a small share of the traffic for fifteen minutes before the rest is updated, and the deployment rolls back automatically when the error rate crosses a threshold. Builds ran on Jenkins in 2020; they run in the shared CI platform today.

## 7. Capacity

The expected peak is a few hundred tokenize calls per second at month end, with detokenize at roughly half that rate. The 2020 sizing assumed fifty calls per second, which was exceeded in the second year. The proposal's figure of one thousand per second was never required. The database runs as a primary with a standby in a second availability zone, and the recovery objective for a regional failure is four hours (the 2020 text said twenty-four hours).

## 8. Detokenization purposes

Detokenization requires a purpose code. The permitted purposes are charge, refund, chargeback and reconciliation. A request with an unknown purpose code is rejected before any data is read. The 2020 text had a fifth purpose, "migration", which was retired when the old system was switched off. The list is reviewed with Compliance once a year.

## 9. Name mapping

| Current name | 2020 name | Proposal name |
|---|---|---|
| tokenization-service | pci-api | tokenizer |
| vault-db | PCI schema on pcidb01 | token store |
| Vault and KMS | file-based key store | hsm-gateway |
| vault private subnet | PCI VLAN | secure segment |

## 10. Open items

- Remove the leftover pci-api dashboards (see the old ticket under the previous project key, link may be dead).
- Update the runbook, which still shows two replicas.
