# fraud scoring infra review (notes)

Attendees: Ivo, Sanjana, Pawel, Mark
Notes: Ivo

## context

Real time fraud scoring replacing the nightly batch. scoring-engine (a.k.a. the scorer) reads payment events from payment-events (MSK), applies rules and the model, writes a decision to decisions-db, and writes an audit record to the scoring audit log group. Terraform: kms scoring_key, msk payment_events, rds decisions_db, security group decisions_sg, log group scoring_audit, iam scoring_policy.

## discussion

**Database.** decisions-db (PostgreSQL) holds every decision together with the customer attributes that were scored. Sanjana asked about sizing, we think about 200 GB for the first year (TBD, depends on the retention discussion in the data section).

**Network.** Pawel asked who can reach the database. The database accepts connections only from the application subnet. Mark will paste the security group rule in the channel later.

**Access to the database.** Agreed without discussion this time.

**Crypto and secrets.** We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode. No secrets are kept in source code, config files, API specs or infrastructure definitions. The approved secret manager is the only source of runtime secrets, fetched at start-up.

The image runs as an unprivileged user and, where possible, mounts its root filesystem read-only.

Traffic between services, and from services to data stores, is encrypted in transit.

Nothing administrative or meant for debugging can be called from outside our network.
Access tokens live for at most 15 minutes, and every refresh token is replaced when it is used.

**Logging.** Authentication failures, privilege changes and access to sensitive data are written to the logs. We scrub logs so that they contain neither secrets, card numbers nor personal data other than opaque identifiers.

Audit logs are tamper-evident and kept for at least a year.

Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.

**Data.** The retention period is 24 months for customer records and 90 days for delivery logs, and expired data is removed by a scheduled deletion job. Open: what the retention period is for review decisions, compliance says 13 months, risk says 24 (TBD). Third parties receive only the fields they need, and only if an approved data processing agreement covers them. At the moment nothing leaves.

**Code and build.** A raw SQL fragment from the query string is appended to the decisions report query, so analysts can add their own conditions. Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks.

## model and rules (short)

The scorer first applies simple rules (same device in three countries in one hour, and similar). A rule with block ends the decision. Otherwise the model produces a score and thresholds map it to allow, review or block. Reasons are stored with the decision. Shadow mode for new model versions was agreed: score everything, act on nothing, compare for two weeks.

## action items

- Mark: security group screenshot.
- Sanjana: decide on partitions for the topic.
- Pawel: write down the retention decision once compliance and risk agree.
- Ivo: clean up the diagram (the old one still shows the batch job).
