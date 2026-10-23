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
- Card numbers are never stored in clear text; they are replaced by tokens from the card token vault.
- Traffic between services, and between services and data stores or brokers, is encrypted in transit.
- We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.
- Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year.
- TLS certificate verification is enabled in all clients, with no option to disable it.
- The database sits in private subnets with no public endpoint.
- Backups are encrypted.
- The service role can only read its own table.

---

## Part B (Tom, service side)

#### tokenizer

so the tokenizer (that's tokenization-service, I always say tokenizer) gets a PAN, asks Vault and KMS for a data key, encrypts, stores, hands back a token. detokenize wants a purpose code, unknown codes are rejected before anything is read. The tokenization-service writes a log line for every tokenize and detokenize call.

#### secrets

Source, config, specs and infrastructure definitions contain no secrets. On boot, the service pulls its credentials from the approved secret store.

#### logging

- The audit trail includes authentication failures, privilege changes and sensitive-data access.

#### test data and code

Real customer and card data is kept out of dev, test and staging. Token lifecycle callbacks, outbound and inbound, are signed and the signatures are verified. All queries use bound parameters instead of string concatenation.

#### build and network

Every build scans libraries and container images, and critical vulnerabilities get a 14-day fix deadline. Containers run as a non-root user, with a read-only root filesystem where possible. Egress is limited to the approved list of third-party destinations.

#### sizing and ops

Peak is a few hundred tokenize calls per second at month end. One instance is enough for launch according to the first estimate, the platform half says two replicas. The recovery objective for a regional failure is four hours. Key rotation runs weekly in staging.

##### Differences between the halves

Part A says "Vault and KMS", Part B sometimes says "the key service". Part A talks about two replicas for production, Part B about one instance. The old design (Vault v1, link dead) used the name vault-svc for the tokenizer.
