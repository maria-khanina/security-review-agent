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

- PII at rest is AES-256 (RDS storage encryption with kms key scoring_key).
- Administrative and debug endpoints must not be reachable from the public internet.
- Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.
- Approved algorithms only; MD5, SHA-1, DES, 3DES and ECB are banned.
- Databases and message brokers must not be publicly reachable and must live in private subnets.
- The audit trail is tamper-evident, and we keep it for no less than twelve months.
- No secrets in code, config, specs or terraform.
- Runtime secrets are read from the secret store when the service starts.
- Auth failures, privilege changes and sensitive data access are logged.
- Workloads are non-root, and read-only root filesystems are used wherever they can be.
- The service connects with its own database account that has only SELECT and INSERT on the tables it uses, because it never updates or deletes rows; no administrative account is shared with other services.
- Logs carry no secrets, card numbers or personal data other than opaque ids.
- Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.
- Backups must be encrypted and restoration must be tested at least twice a year.
- Third-party transfers are covered by an approved data processing agreement and are limited to the listed fields, which the vendor needs to perform the service; all other fields are removed before sending.
- Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
- All db queries are parameterized, no string concatenation of user input.
- CI scans dependencies and images; critical vulns fixed within 14 days.

TBD: autoscaling thresholds for the engine.
TBD: alert routing.
