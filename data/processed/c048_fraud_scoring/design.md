# fraud scoring: boxes and arrows

```
  payment-events (MSK)
          |
          |  payment events + customer attributes
          v
  +-------------------+       risk decisions       +--------------------------+
  |   scoring-engine  |--------------------------->| decisions-db (PostgreSQL) |
  +-------------------+                            +--------------------------+
          |
          |  audit records
          v
  +--------------------------+
  | scoring audit log group  |
  +--------------------------+
```

## Resources (terraform)

| resource | name | role |
|---|---|---|
| kms | scoring_key | encryption keys
| msk | payment_events | input topic |
| rds | decisions_db | decision store |
| sg | decisions_sg | database firewall |
| loggroup | scoring_audit | audit trail |
| iam | scoring_policy | engine role permissions |

## Captions

- Input is the MSK topic only. The engine reads, scores, writes. No other inbound path.
- decisions-db (PostgreSQL) holds the risk decisions together with the customer attributes that were scored.
- Output: decision row + audit record. Nothing leaves the account.

## Notes: access

- Internal service calls to the scoring-engine are authenticated with mutual TLS or signed workload identity tokens.
- Access tokens expire within 15 minutes; refresh tokens are rotated on use.
- The database accepts connections only from the application subnet.

## Notes: crypto and secrets

- Personally identifiable information is encrypted at rest with AES-256.
- Traffic between services, and between services and data stores or brokers, is encrypted in transit.
- Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.
- Services validate TLS certificates and never disable verification.
- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- Runtime secrets are fetched from the approved secret store at startup.

## Notes: data and egress

- Personal data goes to third parties only under an approved data processing agreement, and only the fields required.
- Non-production environments hold no real personal or card data.
- Services that call third parties have egress restricted to an approved allowlist.
- Callbacks on block decisions are signed and signatures verified, outbound and inbound.

## Notes: logging and ops

- Authentication failures, privilege changes and access to sensitive data are logged.
- Database queries are parameterized; concatenating user input into queries is prohibited.
- CI scans dependencies and images; critical vulnerabilities are fixed within 14 days.
- Containers run as a non-root user, with a read-only root filesystem where possible.

TBD: alert thresholds for consumer lag.
TBD: who owns the review queue mailbox.
