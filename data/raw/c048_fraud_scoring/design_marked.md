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
- ⟦F2|decisions-db (PostgreSQL) holds the risk decisions together with the customer attributes that were scored.⟧
- Output: decision row + audit record. Nothing leaves the account.

## Notes: access

- ⟦S:AUTH-02|Internal service calls to the scoring-engine are authenticated with mutual TLS or signed workload identity tokens.⟧
- ⟦S:AUTH-03|Access tokens expire within 15 minutes; refresh tokens are rotated on use.⟧
- ⟦F1|The database accepts connections only from the application subnet.⟧

## Notes: crypto and secrets

- ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧
- ⟦S:CRYPTO-04|Traffic between services, and between services and data stores or brokers, is encrypted in transit.⟧
- ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
- ⟦S:CRYPTO-06|Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.⟧
- ⟦S:CRYPTO-07|Services validate TLS certificates and never disable verification.⟧
- ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧
- ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧

## Notes: data and egress

- ⟦S:DATA-03|Personal data goes to third parties only under an approved data processing agreement, and only the fields required.⟧
- ⟦S:DATA-04|Non-production environments hold no real personal or card data.⟧
- ⟦S:NET-04|Services that call third parties have egress restricted to an approved allowlist.⟧
- ⟦S:API-03|Callbacks on block decisions are signed and signatures verified, outbound and inbound.⟧

## Notes: logging and ops

- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧
- ⟦S:API-05|Database queries are parameterized; concatenating user input into queries is prohibited.⟧
- ⟦S:OPS-01|CI scans dependencies and images; critical vulnerabilities are fixed within 14 days.⟧
- ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧

TBD: alert thresholds for consumer lag.
TBD: who owns the review queue mailbox.
