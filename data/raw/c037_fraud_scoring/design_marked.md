# fraud scoring - infra design

```
  payment-events (MSK)
          |
          |  payment events + customer attrs
          v
  +-----------------+            +-------------------------+
  |  scoring-engine |----------->|  decisions-db (Postgres) |
  +-----------------+  decisions +-------------------------+
          |
          | audit records
          v
  +-------------------------+
  |  scoring audit log grp  |
  +-------------------------+

  kms: scoring_key   iam: scoring_policy   sg: decisions_sg
```

## captions

- MSK topic `payment_events` is the only input. engine reads, scores, writes the decision row. nothing else leaves the box.
- audit goes to cloudwatch log group `scoring_audit` (see wiki page "scoring audit" - TBD link).

## notes

- ⟦S:CRYPTO-01|PII at rest is AES-256 (RDS storage encryption with kms key scoring_key).⟧
- ⟦S:AUTHZ-04|Administrative and debug endpoints must not be reachable from the public internet.⟧
- ⟦S:AUTH-02|Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.⟧
- ⟦S:CRYPTO-05|Approved algorithms only; MD5, SHA-1, DES, 3DES and ECB are banned.⟧
- ⟦S:NET-01|Databases and message brokers must not be publicly reachable and must live in private subnets.⟧
- ⟦S:LOG-03|The audit trail is tamper-evident, and we keep it for no less than twelve months.⟧
- ⟦S:SECRET-01|No secrets in code, config, specs or terraform.⟧
- ⟦S:SECRET-02|Runtime secrets are read from the secret store when the service starts.⟧
- ⟦S:LOG-01|Auth failures, privilege changes and sensitive data access are logged.⟧
- ⟦S:OPS-02|Workloads are non-root, and read-only root filesystems are used wherever they can be.⟧
- ⟦S:AUTHZ-03|The application never uses a shared administrative database login; it has a dedicated, minimally privileged account.⟧
- ⟦S:LOG-02|Logs carry no secrets, card numbers or personal data other than opaque ids.⟧
- ⟦S:DATA-02|Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.⟧
- ⟦S:OPS-03|Backups must be encrypted and restoration must be tested at least twice a year.⟧
- ⟦S:DATA-03|No third parties receive this data; any future transfer only under an approved DPA and with just the required fields.⟧
- ⟦S:AUTH-03|Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.⟧
- ⟦S:API-05|All db queries are parameterized, no string concatenation of user input.⟧
- ⟦S:OPS-01|CI scans dependencies and images; critical vulns fixed within 14 days.⟧

TBD: autoscaling thresholds for the engine.
TBD: alert routing.
