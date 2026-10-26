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
- ⟦F1|decisions-db (PostgreSQL) holds the risk decisions together with the customer attributes that were scored.⟧
- Output: decision row + audit record. Nothing leaves the account.

## Notes: access

- ⟦S:AUTH-02|We do not trust the internal network by itself: every internal call is authenticated with mTLS or workload identity tokens.⟧
- ⟦S:AUTH-03|Access tokens expire within 15 minutes; refresh tokens are rotated on use.⟧
- ⟦S:LOG-04|Only authorized staff can access the central logs.⟧
- ⟦S:LOG-02|Nothing sensitive is logged: no secrets, no card numbers, and no personal data beyond opaque ids.⟧
- The database accepts connections only from the application subnet.

## Notes: crypto and secrets

- ⟦S:CRYPTO-01|Encryption at rest with AES-256 covers personal data in databases and object storage, and its keys live in the corporate key management service.⟧
- ⟦S:CRYPTO-04|Traffic between services, and between services and data stores or brokers, is encrypted in transit.⟧
- ⟦S:CRYPTO-05|The approved algorithm list is followed, and MD5, SHA-1, DES, 3DES and ECB mode are prohibited in this service.⟧
- ⟦S:AUTHZ-02|Internal users must receive only the roles required for their job and roles must be defined per service.⟧
- ⟦S:CRYPTO-06|Key material is kept in KMS and separate from the data, and keys are rotated every year or sooner.⟧
- ⟦S:CRYPTO-07|TLS certificate verification is enabled in all clients, with no option to disable it.⟧
- ⟦S:SECRET-01|No secrets are kept in source code, config files, API specs or infrastructure definitions.⟧
- ⟦S:AUTHZ-03|The service connects to its database with its own account, which has only the grants it needs.⟧
- ⟦S:SECRET-02|Runtime secrets are read from the secret store when the service starts.⟧

## Notes: data and egress

- ⟦S:DATA-03|Third parties receive only the fields they need, and only if an approved data processing agreement covers them.⟧
- ⟦S:LOG-03|The audit trail is tamper-evident, and we keep it for no less than twelve months.⟧
- ⟦F2|Support analysts reproduce scoring issues in staging with real customer records.⟧
- ⟦S:NET-04|Services that call third parties have egress restricted to an approved allowlist.⟧
- ⟦S:API-03|Every webhook we send or receive is signed with an HMAC, and the receiver checks the signature together with the timestamp.⟧

## Notes: logging and ops

- ⟦S:LOG-01|We log failed logins, changes of privileges and reads of sensitive data.⟧
- ⟦S:API-05|User input reaches the database only as query parameters, never as part of the query text.⟧
- ⟦S:OPS-01|Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less.⟧
- ⟦S:OPS-02|The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only.⟧

TBD: alert thresholds for consumer lag.
TBD: who owns the review queue mailbox.
