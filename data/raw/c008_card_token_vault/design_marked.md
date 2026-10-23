# Card token vault: infra design sync (notes)

Attendees: Priya, Tomas, Lena, Mark (infra), someone from compliance (name TBD)
Notes by: Tomas

## What we are building

The vault tokenizes card numbers (PANs) for the other payment services. Payment services send a PAN to the token service (tokenization-service, sometimes called "the tokenizer" or "vault-svc" in the old slides) and get a token back; to charge a card later they send the token and the vault gives back the PAN for the acquirer call. Everything runs in the vault private subnet (also called the PCI subnet in Lena's diagrams). Same thing, two names, we should pick one. Decision: "vault private subnet".

Pieces in terraform:
- kms key `vault_key` for data keys
- RDS Postgres `vault_db` (card data, encrypted fields)
- security group `vault_db_sg`
- CloudWatch log group `vault_audit`
- backup vault `vault_backups`
- IAM policy `vault_service_policy` for the service role

## Data flow

1. Payment service -> tokenization-service: PAN in, token out (tokenize) or token in, PAN out (detokenize).
2. tokenization-service -> vault-db: stores the card data in encrypted form.
3. tokenization-service -> Vault and KMS: asks for data encryption keys.

## Discussion

**Network.** Mark wanted to know who can reach the database. ⟦F3|The database accepts connections only from the application subnet.⟧ Tomas will double check the security group rule before we sign off (TBD).

**Storage of PANs.** ⟦S:CRYPTO-02|Primary account numbers are never stored in clear text and are tokenized by the card token vault; no other service keeps them.⟧ Lena asked about the old refund tables in the payments service, they still hold masked values only. OK.

**Database.** ⟦F1|vault-db (PostgreSQL) holds the encrypted card records and runs as a single instance with a standby.⟧ Priya said the standby plan is TBD, we come back to it next week.

**Service-to-service.** ⟦S:AUTH-02|Calls from payment services to the tokenization service are authenticated with mutual TLS or signed workload identity tokens.⟧ We argued about which of the two for a while. Outcome: mTLS first, tokens only if mTLS is a blocker (TBD, Mark to check the mesh).

**Application.** ⟦F2|tokenization-service is a small Go service with two handlers and a worker that rotates data keys.⟧ ⟦S:API-05|Database queries are parameterized, and user input is never concatenated into SQL.⟧

**Logging.** ⟦F4|tokenization-service writes structured logs for every tokenize and detokenize call.⟧ ⟦S:LOG-01|The audit trail includes authentication failures, privilege changes and sensitive-data access.⟧ Open: where audit logs go besides the log group (TBD).

## Access and secrets

- ⟦S:AUTHZ-02|Internal users are given the minimum set of roles for their job, and roles are defined service by service.⟧ Compliance wants the role list as an appendix.
- ⟦S:AUTHZ-05|Access to production is recertified at least once per quarter.⟧ Owner: Lena (confirmed this time, previously "infra team").
- ⟦S:SECRET-01|No secrets are kept in source code, config files, API specs or infrastructure definitions.⟧
- ⟦S:CRYPTO-05|The approved algorithm list is followed, and MD5, SHA-1, DES, 3DES and ECB mode are prohibited in this service.⟧

## Sizing and operations (rough)

- Peak load: about 400 tokenize calls per second at the end of the month, detokenize a bit less. Tomas thinks one instance is fine for launch (TBD, needs load test).
- Key rotation worker: runs weekly in staging first. The schedule for production is not decided.
- Failure mode: if the vault is down, payment services fall back to "retry later" and do not cache PANs anywhere. This was agreed at the very start and nobody objected.

## Action items

- Tomas: verify the security group rule and post the screenshot in the channel.
- Priya: write down the standby plan (TBD).
- Mark: mesh check for mTLS.
- Lena: role appendix for compliance, see the old confluence page "PCI scope" (link broken, find the new one).
- Everyone: stop saying "vault-svc".
