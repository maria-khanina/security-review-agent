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
- Service credentials must be rotated at least every 90 days and immediately after suspected exposure.
- Access tokens are valid for 24 hours or longer, and refresh tokens are not rotated.
- The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.
- Card numbers are never stored in clear text; they are replaced by tokens from the card token vault.
- Traffic between services, and between services and data stores or brokers, is encrypted in transit.
- Access to the centralized logging system is restricted to authorized people.
- We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.
- Each service has a dedicated database user limited to the tables and operations it uses, and administrative credentials are not shared.
- Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year.
- TLS certificate verification is enabled in all clients, with no option to disable it.
- Requests from outside are checked against the schema and rejected if they do not conform.
- The database and the message broker are in private subnets with no public address.
- Audit logs must be tamper-evident and retained for at least one year.
- Databases and buckets that hold personal data use AES-256 encryption at rest, and the keys are managed in the corporate key management service.
- The database sits in private subnets with no public endpoint.
- Backups are encrypted.
- The service role can only read its own table.

---

## Part B (Tom, service side)

#### tokenizer

so the tokenizer (that's tokenization-service, I always say tokenizer) gets a PAN, asks Vault and KMS for a data key, encrypts, stores, hands back a token. detokenize wants a purpose code, unknown codes are rejected before anything is read. The tokenization-service writes a log line for every tokenize and detokenize call.

#### secrets

Source, config, specs and infrastructure definitions contain no secrets. On boot, the service pulls its credentials from the approved secret store.

Every request for a customer-owned resource must verify that the caller owns or is entitled to that resource.

#### logging

- The audit trail includes authentication failures, privilege changes and sensitive-data access.
- Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.

#### test data and code

Real customer and card data is kept out of dev, test and staging. Webhook payloads are HMAC-signed and timestamped, and the receiver verifies the signature and the timestamp before accepting them. All queries use bound parameters instead of string concatenation.

Backups must be encrypted and restoration must be tested at least twice a year.

#### build and network

Every build scans libraries and container images, and critical vulnerabilities get a 14-day fix deadline. Containers run as a non-root user, with a read-only root filesystem where possible. Egress is limited to the approved list of third-party destinations.

#### sizing and ops

Peak is a few hundred tokenize calls per second at month end. One instance is enough for launch according to the first estimate, the platform half says two replicas. The recovery objective for a regional failure is four hours. Key rotation runs weekly in staging.

##### Differences between the halves

Part A says "Vault and KMS", Part B sometimes says "the key service". Part A talks about two replicas for production, Part B about one instance. The old design (Vault v1, link dead) used the name vault-svc for the tokenizer.
