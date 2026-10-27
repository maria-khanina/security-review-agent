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

- We do not trust the internal network by itself: every internal call is authenticated with mTLS or workload identity tokens.
- Access tokens expire within 15 minutes; refresh tokens are rotated on use.
- Only the support engineers of this service and the security analysts can read the central logs, because they use them to resolve customer tickets and to review security events; nobody else has access.
- Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids.
- The database accepts connections only from the application subnet.

## Notes: crypto and secrets

- Encryption at rest with AES-256 covers personal data in databases and object storage, and its keys live in the corporate key management service.
- Traffic between services, and between services and data stores or brokers, is encrypted in transit.
- The approved algorithm list is followed, and MD5, SHA-1, DES, 3DES and ECB mode are prohibited in this service.
- The service defines three roles of its own: operator, auditor and administrator; operators need write access to run the daily jobs, auditors only read, and administrators are limited to the platform team.
- Key material is kept in KMS and separate from the data, and keys are rotated every year or sooner.
- TLS certificate verification is enabled in all clients, with no option to disable it.
- No secrets are kept in source code, config files, API specs or infrastructure definitions.
- Each service has a dedicated database account; this one is granted read access to the orders table and write access to its audit table only, since those are the only tables its functions touch.
- Runtime secrets are read from the secret store when the service starts.

## Notes: data and egress

- Third parties receive only the fields they need, and only if an approved data processing agreement covers them.
- The audit trail is tamper-evident, and we keep it for no less than twelve months.
- Support analysts reproduce scoring issues in staging with real customer records.
- Services that call third parties have egress restricted to an approved allowlist.
- Every webhook we send or receive is signed with an HMAC, and the receiver checks the signature together with the timestamp.

## Notes: logging and ops

- We log failed logins, changes of privileges and reads of sensitive data.
- User input reaches the database only as query parameters, never as part of the query text.
- Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less.
- The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only.

TBD: alert thresholds for consumer lag.
TBD: who owns the review queue mailbox.
