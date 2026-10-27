# vault sync, infra + security (notes)

Attendees: Priya, Tomas, Lena, Mark, someone from compliance (name TBD)
Notes: Mark

## what we talked about

The vault tokenizes card numbers (PANs) for the payment services. Payment services send a PAN to tokenization-service (the tokenizer, "vault-svc" on Priya's slides, we should stop using that name) and get a token back. Later they send the token and get the PAN back for the acquirer call. Everything sits in the vault private subnet (Lena calls it the PCI subnet, same thing). Behind the service there is vault-db (PostgreSQL) and Vault and KMS for the keys and runtime secrets. Terraform has six resources: kms vault_key, rds vault_db, security group vault_db_sg, log group vault_audit, backup vault vault_backups and iam policy vault_service_policy.

## decisions

- **Service auth.** ⟦S:AUTH-02|Calls from payment services to the tokenization-service are authenticated with mutual TLS or signed workload identity tokens.⟧ Argued about mTLS vs tokens for 20 minutes. Decision: mTLS first, tokens if the mesh is a blocker (Mark to check, TBD).

⟦S:LOG-02|Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids.⟧
- **Tokens.** Where tokens are used, ⟦S:AUTH-03|access tokens expire within 15 minutes and refresh tokens are rotated on use.⟧

⟦S:DATA-03|Data goes to the processor under the signed data processing agreement and only the fields it needs for the contracted task are sent: the order reference and the delivery address, because nothing else is required for delivery.⟧
- **Roles.** Roles: operator, auditor, key custodian.
- **Database account.**
- **PANs.** ⟦S:CRYPTO-02|The PAN is tokenized by the card token vault and only the token is kept.⟧ Lena confirmed the old refund tables only hold masked values.
- **Transport.** ⟦S:CRYPTO-04|Traffic between services, and between services and data stores or brokers, is encrypted in transit.⟧ ⟦S:CRYPTO-07|TLS certificate verification is enabled in all clients, with no option to disable it.⟧
- **Algorithms and keys.** ⟦S:CRYPTO-05|Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.⟧ ⟦S:CRYPTO-06|Keys are managed in KMS, never stored next to the encrypted data, and rotated annually.⟧

⟦S:API-04|Clients get generic error messages without stack traces, SQL or internal hostnames.⟧
⟦S:DATA-01|A register of personal fields with the purpose of each is kept for the service, and anything that is not in the register is not stored.⟧

## secrets and network

- ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧
- ⟦S:AUTHZ-01|The service compares the authenticated caller with the owner of the requested resource and rejects the request if they do not match and no entitlement exists.⟧
- ⟦S:SECRET-02|At startup the service fetches its secrets from the approved secret store.⟧
- ⟦S:AUTHZ-02|Staff receive only the roles their job requires: support agents get the viewer role because they answer tickets, engineers get the operator role because they deploy and debug, and nobody gets the administrator role by default.⟧
- Owner for the rotation job: Tomas (confirmed this time).
- ⟦S:NET-01|vault-db and the message brokers sit in private subnets and are not publicly reachable.⟧
- ⟦S:NET-04|Outbound calls to third parties are restricted to an approved allowlist.⟧ Right now the vault calls nobody outside, so this is a guard for later.

## logging

- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧

## build, test, ops

- ⟦S:DATA-04|Non-production environments contain no real personal or card data.⟧ Staging uses test PANs from the card network test ranges.
- ⟦S:API-03|Inbound and outbound webhooks include an HMAC signature and a timestamp; verification of both is mandatory on the receiving side.⟧
- ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧
- ⟦S:OPS-03|We encrypt backups and run a restore test at least twice a year.⟧
- ⟦S:OPS-01|Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks.⟧
- ⟦S:OPS-02|No container runs as root, and the root filesystem is read-only wherever possible.⟧
- ⟦S:CRYPTO-01|At rest, personal data is protected with AES-256 in both the database and object storage, with keys from the corporate key management service.⟧

## sizing (rough)

- Peak about 400 tokenize calls per second at month end, detokenize a bit less. One instance is probably fine for launch (TBD, needs a load test).
- Regional recovery goal: four hours. Restore into the standby region is in the runbook (old runbook link is dead, Lena will find the new one).

## action items

- Mark: mesh check for mTLS.
- Tomas: write the rotation job.
- Priya: standby plan for the database.
- Lena: role list for compliance.
- All: say "tokenizer", not "vault-svc".
