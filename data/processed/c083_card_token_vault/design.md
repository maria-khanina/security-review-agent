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
- Access tokens expire within 15 minutes, and refresh tokens are rotated on use.
- Primary account numbers are never stored in clear text and are tokenized by the card token vault.
- Traffic between services, and between services and data stores or brokers, is encrypted in transit.
- Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.
- Services validate TLS certificates and never disable verification.
- vault-db and the message brokers sit in private subnets and are not publicly reachable.
- Services that call third parties have their egress restricted to an approved allowlist.

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

- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- Runtime secrets are fetched from the approved secret store at startup.

#### logs

| what | rule |
|---|---|
| security events | Authentication failures, privilege changes and access to sensitive data are logged. |
| audit |

#### test data, queries, build, backups

Non-production environments do not contain real personal or card data. Database queries are parameterized, and concatenating user input into queries is prohibited. The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.

#### sizing

Peak is a few hundred tokenize calls per second at month end, detokenize about half of that. The database runs as a primary with a standby in a second availability zone and the recovery objective for a regional failure is four hours. A key rotation worker runs weekly in staging; the production schedule is not fixed.

##### Differences between the halves

Part A says three replicas, Part B says two. Part A says "vault-db", Part B once says "the card store". To be reconciled before review.
