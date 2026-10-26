# Card Token Vault Design

## Part A (Arjun, infrastructure side)

### 1. Overview

The vault tokenizes primary account numbers (PANs) for the payment services. It is the only component that stores PANs. It runs in the vault private subnet.

### 2. Components

- tokenization-service: tokenize (PAN in, token out) and detokenize (token in, PAN out).
- vault-db (PostgreSQL): encrypted card records and the token mapping.
- Vault and KMS: data encryption keys and runtime secrets.
- vault private subnet: network boundary.

### 3. Terraform resources

- KMS key `vault_key`
- database `vault_db`
- security group `vault_db_sg`
- log group `vault_audit`
- backup vault `vault_backups`
- IAM policy `vault_service_policy`

### 4. Security (infrastructure view)

- Calls from payment services to the tokenization-service are authenticated with mutual TLS or signed workload identity tokens.
- A caller can only read or change resources that belong to them or that they have been explicitly granted.
- A register of personal fields with the purpose of each is kept for the service, and anything that is not in the register is not stored.
- The vendor receives the complete customer profile, including fields it does not need, and there is no signed data processing agreement with them.
- The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.
- Each export file is encrypted at rest, readable only by the authorized requester, and removed automatically after 72 hours.
- Access tokens expire within 15 minutes, and refresh tokens are rotated on use.
- We do not keep primary account numbers: the card token vault tokenizes them and we store the token.
- Traffic between services, and between services and data stores or brokers, is encrypted in transit.
- Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.
- Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.
- Clients check the certificate chain and host name on every TLS connection and have no insecure mode.
- Clients get generic error messages without stack traces, SQL or internal hostnames.
- Encryption at rest with AES-256 covers personal data in databases and object storage, and its keys live in the corporate key management service.
- vault-db and the message brokers sit in private subnets and are not publicly reachable.
- We keep personal data for 12 months at most and delete it automatically when the period ends, or earlier on a verified request.
- Third-party calls leave through an egress allowlist, not through open outbound access.

### 5. Deployment (platform view)

The tokenization-service runs as three replicas behind an internal load balancer. Rolling updates replace one replica at a time.

---

## Part B (Mei, service side)

#### what the "tokenizer" does

The tokenizer (tokenization-service, I say tokenizer) takes a PAN, encrypts it with a data key from Vault and KMS, writes it and gives a token back. Detokenize needs a purpose code. The tokenizer sends token lifecycle events (created, rotated, revoked) to the payment services as callbacks. Our runs two replicas, not three, in the current setup (the infra half says three).

#### permissions

The service role can only read its own table. Everything else the service needs is granted explicitly in the IAM policy.

#### containers

The container user is not set, so processes run as root. It never mattered for the file permissions so far and we left it.

#### secrets

- Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.
- At startup the service fetches its secrets from the approved secret store.
- We encrypt backups and run a restore test at least twice a year.

#### logs

| what | rule |
|---|---|
| security events | The audit trail includes authentication failures, privilege changes and sensitive-data access. |
| audit |

#### test data, queries, build, backups

Test and staging environments use synthetic data, never real personal data or card data. User input reaches the database only as query parameters, never as part of the query text. Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less.

The application never uses a shared administrative database login; it has a dedicated, minimally privileged account.

Schema validation runs on every external input, and invalid data never reaches the business logic.

#### sizing

Peak is a few hundred tokenize calls per second at month end, detokenize about half of that. The database runs as a primary with a standby in a second availability zone and the recovery objective for a regional failure is four hours. A key rotation worker runs weekly in staging; the production schedule is not fixed.

##### Differences between the halves

Part A says three replicas, Part B says two. Part A says "vault-db", Part B once says "the card store". To be reconciled before review.
