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
- ⟦S:CRYPTO-05|Approved algorithms only; MD5, SHA-1, DES, 3DES and ECB are banned.⟧
- ⟦S:SECRET-01|No secrets in code, config, specs or terraform.⟧
- ⟦S:SECRET-02|Runtime secrets are read from the secret store when the service starts.⟧
- ⟦S:LOG-01|Auth failures, privilege changes and sensitive data access are logged.⟧
- ⟦S:LOG-02|Logs carry no secrets, card numbers or personal data other than opaque ids.⟧
- ⟦S:DATA-02|Decisions carrying personal data have a 13 month retention, then a scheduled job deletes them (also on verified deletion request).⟧
- ⟦S:DATA-03|No third parties receive this data; any future transfer only under an approved DPA and with just the required fields.⟧
- ⟦S:API-05|All db queries are parameterized, no string concatenation of user input.⟧
- ⟦S:OPS-01|CI scans dependencies and images; critical vulns fixed within 14 days.⟧

TBD: autoscaling thresholds for the engine.
TBD: alert routing.
