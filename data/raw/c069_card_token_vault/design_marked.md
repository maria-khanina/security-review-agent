# vault sync, infra + security (notes)

Attendees: Priya, Tomas, Lena, Mark, someone from compliance (name TBD)
Notes: Mark

## what we talked about

The vault tokenizes card numbers (PANs) for the payment services. Payment services send a PAN to tokenization-service (the tokenizer, "vault-svc" on Priya's slides, we should stop using that name) and get a token back. Later they send the token and get the PAN back for the acquirer call. Everything sits in the vault private subnet (Lena calls it the PCI subnet, same thing). Behind the service there is vault-db (PostgreSQL) and Vault and KMS for the keys and runtime secrets. Terraform has six resources: kms vault_key, rds vault_db, security group vault_db_sg, log group vault_audit, backup vault vault_backups and iam policy vault_service_policy.

## decisions

- **Service auth.** ⟦S:AUTH-02|Calls from payment services to the tokenization-service are authenticated with mutual TLS or signed workload identity tokens.⟧ Argued about mTLS vs tokens for 20 minutes. Decision: mTLS first, tokens if the mesh is a blocker (Mark to check, TBD).
- **Tokens.** Where tokens are used, ⟦S:AUTH-03|access tokens expire within 15 minutes and refresh tokens are rotated on use.⟧
- **Roles.** Roles: operator, auditor, key custodian.
- **Database account.**
- **PANs.** ⟦S:CRYPTO-02|The PAN is tokenized by the card token vault and only the token is kept.⟧ Lena confirmed the old refund tables only hold masked values.
- **Transport.** ⟦S:CRYPTO-04|Traffic between services, and between services and data stores or brokers, is encrypted in transit.⟧ ⟦S:CRYPTO-07|TLS certificate verification is enabled in all clients, with no option to disable it.⟧
- **Algorithms and keys.** ⟦S:CRYPTO-05|Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.⟧ ⟦S:CRYPTO-06|Keys are managed in KMS, never stored next to the encrypted data, and rotated annually.⟧

## secrets and network

- ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧
- ⟦S:SECRET-02|At startup the service fetches its secrets from the approved secret store.⟧
- Owner for the rotation job: Tomas (confirmed this time).
- ⟦S:NET-01|vault-db and the message brokers sit in private subnets and are not publicly reachable.⟧
- ⟦S:NET-04|Outbound calls to third parties are restricted to an approved allowlist.⟧ Right now the vault calls nobody outside, so this is a guard for later.

## logging

- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧

## build, test, ops

- ⟦S:DATA-04|Non-production environments contain no real personal or card data.⟧ Staging uses test PANs from the card network test ranges.
- ⟦S:API-03|Token lifecycle callbacks, outbound and inbound, are signed and the signatures are verified.⟧
- ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧
- ⟦S:OPS-01|Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks.⟧
- ⟦S:OPS-02|No container runs as root, and the root filesystem is read-only wherever possible.⟧

## sizing (rough)

- Peak about 400 tokenize calls per second at month end, detokenize a bit less. One instance is probably fine for launch (TBD, needs a load test).
- Regional recovery goal: four hours. Restore into the standby region is in the runbook (old runbook link is dead, Lena will find the new one).

## action items

- Mark: mesh check for mTLS.
- Tomas: write the rotation job.
- Priya: standby plan for the database.
- Lena: role list for compliance.
- All: say "tokenizer", not "vault-svc".
