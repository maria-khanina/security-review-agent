# Engineering Security Handbook

A short reference for engineers building Meridian Pay services. It summarizes the requirements from the Information Security Policy that most often come up in design reviews. MUST means mandatory. SHOULD means expected unless there is a documented reason.

## Authentication and Authorization

- Public endpoints MUST require OAuth2/OIDC bearer tokens or mutual TLS.
- Services SHOULD authenticate each other with mutual TLS or workload identity tokens.
- Access tokens MUST expire within 15 minutes. Refresh tokens MUST be rotated on use.
- Passwords MUST be hashed with argon2id or bcrypt.
- A service MUST check that the caller is allowed to access the specific record requested.
- Each service SHOULD use its own database account with the least privilege required.
- Admin and debug endpoints MUST NOT be exposed to the public internet.
- For long-lived sessions, an access token lifetime of up to 30 minutes is acceptable.

## Data and Cryptography

- Personal data at rest MUST be encrypted with AES-256.
- Card numbers MUST NOT be stored. Use tokens from the card token vault.
- External traffic MUST use TLS 1.2 or higher.
- Legacy partner endpoints may use TLS 1.0 until they have migrated.
- Internal traffic SHOULD be encrypted in transit.
- MD5, SHA-1, DES and ECB mode MUST NOT be used.
- Personal data MUST have a retention period and a deletion process.
- Sending personal data to a vendor MUST be covered by a data processing agreement, and you MUST send only the fields the vendor needs.
- Backups should be encrypted and restore procedures tested regularly.

## Secrets and Infrastructure

- Secrets MUST NOT be committed to code, configuration or specs.
- Services MUST fetch secrets from the secret store at runtime.
- Databases and brokers MUST be in private subnets.
- Reporting replicas may be exposed through an allowlisted public endpoint when an external vendor requires it.
- Buckets MUST block public access.
- SSH, RDP and database ports MUST NOT be open to the world.
- Public services SHOULD be behind a WAF.
- Containers SHOULD run as non-root.
- Pipelines MUST scan dependencies for known vulnerabilities.

## Application Security and Logging

- Validate all external input against a schema.
- Public APIs MUST be protected against excessive use.
- Use parameterized queries only.
- Browsers MUST be allowed to call our APIs only from approved origins through restricted CORS.
- Log authentication failures, privilege changes and sensitive data access.
- Never log secrets, card numbers or personal data other than opaque ids.
- Audit logs MUST be kept long enough to meet regulatory obligations.
