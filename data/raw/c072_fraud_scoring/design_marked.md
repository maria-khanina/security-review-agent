# fraud scoring infra review (notes)

Attendees: Ivo, Sanjana, Pawel, Mark
Notes: Ivo

## context

Real time fraud scoring replacing the nightly batch. scoring-engine (a.k.a. the scorer) reads payment events from payment-events (MSK), applies rules and the model, writes a decision to decisions-db, and writes an audit record to the scoring audit log group. Terraform: kms scoring_key, msk payment_events, rds decisions_db, security group decisions_sg, log group scoring_audit, iam scoring_policy.

## discussion

**Database.** ⟦F2|decisions-db (PostgreSQL) holds every decision together with the customer attributes that were scored.⟧ Sanjana asked about sizing, we think about 200 GB for the first year (TBD, depends on the retention discussion in the data section).

**Network.** Pawel asked who can reach the database. ⟦F1|The database accepts connections only from the application subnet.⟧ Mark will paste the security group rule in the channel later.

**Access to the database.** Agreed without discussion this time.

**Crypto and secrets.** ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧ ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧

**Logging.** ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧ ⟦S:LOG-02|Logs contain no secrets, card numbers or personal data beyond opaque identifiers.⟧

**Data.** ⟦S:DATA-02|Personal data has a defined retention period and is deleted when it expires or on a verified request from the data subject.⟧ Open: what the retention period is for review decisions, compliance says 13 months, risk says 24 (TBD). ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧ At the moment nothing leaves.

**Code and build.** ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧ ⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧

## model and rules (short)

The scorer first applies simple rules (same device in three countries in one hour, and similar). A rule with block ends the decision. Otherwise the model produces a score and thresholds map it to allow, review or block. Reasons are stored with the decision. Shadow mode for new model versions was agreed: score everything, act on nothing, compare for two weeks.

## action items

- Mark: security group screenshot.
- Sanjana: decide on partitions for the topic.
- Pawel: write down the retention decision once compliance and risk agree.
- Ivo: clean up the diagram (the old one still shows the batch job).
