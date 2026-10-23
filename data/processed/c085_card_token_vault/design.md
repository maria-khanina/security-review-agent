# Card Token Vault Design

## Part A (Priya, architecture)

### 1. Purpose

The card token vault tokenizes primary account numbers (PANs) for the payment services and is the only component that stores them. All other services handle tokens.

### 2. Components

- tokenization-service: tokenize and detokenize.
- vault-db (PostgreSQL): encrypted card records and the token mapping.
- Vault and KMS: data encryption keys and runtime secrets.
- vault private subnet: the network around the vault.

### 3. Infrastructure

Terraform declares the KMS key `vault_key`, the database `vault_db`, the security group `vault_db_sg`, the log group `vault_audit`, the backup vault `vault_backups` and the IAM policy `vault_service_policy`.

### 4. Security (architecture view)

- Calls from payment services to the tokenization-service are authenticated with mutual TLS or signed workload identity tokens.
- Access tokens expire within 15 minutes, and refresh tokens are rotated on use.
- Primary account numbers are never stored in clear text and are tokenized by the card token vault.
- Traffic between services, and between services and data stores or brokers, is encrypted in transit.
- Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.
- Services validate TLS certificates and never disable verification.
- The database sits in private subnets with no public endpoint.
- Backups are encrypted.
- The service role can only read its own table.

---

## Part B (Tom, service side)

#### tokenizer

so the tokenizer (that's tokenization-service, I always say tokenizer) gets a PAN, asks Vault and KMS for a data key, encrypts, stores, hands back a token. detokenize wants a purpose code, unknown codes are rejected before anything is read. The tokenization-service writes a log line for every tokenize and detokenize call.

#### secrets

Secrets do not appear in source code, configuration files, specifications or infrastructure definitions. Runtime secrets are fetched from the approved secret store at startup.

#### logging

- Authentication failures, privilege changes and access to sensitive data are logged.

#### test data and code

Non-production environments do not contain real personal or card data. Token lifecycle callbacks, outbound and inbound, are signed and the signatures are verified. Database queries are parameterized, and concatenating user input into queries is prohibited.

#### build and network

The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days. Containers run as a non-root user, with a read-only root filesystem where possible. Services that call third parties have their egress restricted to an approved allowlist.

#### sizing and ops

Peak is a few hundred tokenize calls per second at month end. One instance is enough for launch according to the first estimate, the platform half says two replicas. The recovery objective for a regional failure is four hours. Key rotation runs weekly in staging.

##### Differences between the halves

Part A says "Vault and KMS", Part B sometimes says "the key service". Part A talks about two replicas for production, Part B about one instance. The old design (Vault v1, link dead) used the name vault-svc for the tokenizer.
