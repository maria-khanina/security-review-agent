# vault sync, infra + security (notes)

Attendees: Priya, Tomas, Lena, Mark, someone from compliance (name TBD)
Notes: Mark

## what we talked about

The vault tokenizes card numbers (PANs) for the payment services. Payment services send a PAN to tokenization-service (the tokenizer, "vault-svc" on Priya's slides, we should stop using that name) and get a token back. Later they send the token and get the PAN back for the acquirer call. Everything sits in the vault private subnet (Lena calls it the PCI subnet, same thing). Behind the service there is vault-db (PostgreSQL) and Vault and KMS for the keys and runtime secrets. Terraform has six resources: kms vault_key, rds vault_db, security group vault_db_sg, log group vault_audit, backup vault vault_backups and iam policy vault_service_policy.

## decisions

- **Service auth.** Calls from payment services to the tokenization-service are authenticated with mutual TLS or signed workload identity tokens. Argued about mTLS vs tokens for 20 minutes. Decision: mTLS first, tokens if the mesh is a blocker (Mark to check, TBD).

Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids.
- **Tokens.** Where tokens are used, access tokens expire within 15 minutes and refresh tokens are rotated on use.

Personal data may be sent to third parties only under an approved data processing agreement and only the fields required.
- **Roles.** Roles: operator, auditor, key custodian.
- **Database account.**
- **PANs.** The PAN is tokenized by the card token vault and only the token is kept. Lena confirmed the old refund tables only hold masked values.
- **Transport.** Traffic between services, and between services and data stores or brokers, is encrypted in transit. TLS certificate verification is enabled in all clients, with no option to disable it.
- **Algorithms and keys.** Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned. Keys are managed in KMS, never stored next to the encrypted data, and rotated annually.

Clients get generic error messages without stack traces, SQL or internal hostnames.
A register of personal fields with the purpose of each is kept for the service, and anything that is not in the register is not stored.

## secrets and network

- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- The service compares the authenticated caller with the owner of the requested resource and rejects the request if they do not match and no entitlement exists.
- At startup the service fetches its secrets from the approved secret store.
- Staff roles are limited to what each job needs, and every service defines its own roles.
- Owner for the rotation job: Tomas (confirmed this time).
- vault-db and the message brokers sit in private subnets and are not publicly reachable.
- Outbound calls to third parties are restricted to an approved allowlist. Right now the vault calls nobody outside, so this is a guard for later.

## logging

- Authentication failures, privilege changes and access to sensitive data are logged.

## build, test, ops

- Non-production environments contain no real personal or card data. Staging uses test PANs from the card network test ranges.
- Inbound and outbound webhooks include an HMAC signature and a timestamp; verification of both is mandatory on the receiving side.
- Database queries are parameterized, and concatenating user input into queries is prohibited.
- We encrypt backups and run a restore test at least twice a year.
- Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks.
- No container runs as root, and the root filesystem is read-only wherever possible.
- At rest, personal data is protected with AES-256 in both the database and object storage, with keys from the corporate key management service.

## sizing (rough)

- Peak about 400 tokenize calls per second at month end, detokenize a bit less. One instance is probably fine for launch (TBD, needs a load test).
- Regional recovery goal: four hours. Restore into the standby region is in the runbook (old runbook link is dead, Lena will find the new one).

## action items

- Mark: mesh check for mTLS.
- Tomas: write the rotation job.
- Priya: standby plan for the database.
- Lena: role list for compliance.
- All: say "tokenizer", not "vault-svc".
