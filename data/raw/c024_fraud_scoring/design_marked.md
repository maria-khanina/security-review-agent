# Fraud Scoring Service: A Guided Design (for new joiners)

Author: Ivo, Risk Engineering (junior)
Reviewer: Sanjana

## 1. What problem are we solving?

Every time a customer pays, we want to know quickly if the payment looks suspicious. A fraud score is a number that says how risky a payment is. If the score is low we allow the payment, if it is medium we send it to a human to review, and if it is high we block it. This service calculates the score and stores the decision.

## 2. The building blocks

- **payment-events (MSK).** MSK is the managed Kafka from AWS. Kafka is like a conveyor belt where services put messages and other services take them off. Every payment puts an event on the belt.
- **scoring-engine.** This reads each event, applies the rules and the model and produces a decision.
- **decisions-db (PostgreSQL).** The engine writes the decision here, together with the customer attributes it used.
- **scoring audit log group.** A place in CloudWatch where the engine writes an audit record for every decision.

## 3. How a payment gets scored

The flow has three arrows. First, payment-events sends the payment event to the scoring-engine, with customer attributes such as country, device id and the history counters. Second, the scoring-engine writes the risk decision to decisions-db. Third, the scoring-engine writes an audit record to the scoring audit log group. We are not using any other storage, so there are only three arrows to understand.

## 4. The infrastructure files

Everything is created with Terraform, which means that infrastructure is described in files. There are six resources:

- `scoring_key`, a KMS key used for encryption;
- `payment_events`, the MSK cluster;
- `decisions_db`, the PostgreSQL database on RDS;
- `decisions_sg`, a security group, which is a firewall for the database;
- `scoring_audit`, the log group;
- `scoring_policy`, the IAM policy that says what the engine is allowed to do in AWS.

## 5. Who is calling whom?

Authentication means checking who the caller is. ⟦S:AUTH-02|Internal service calls to the scoring-engine are authenticated with mutual TLS or signed workload identity tokens.⟧ When tokens are used, ⟦S:AUTH-03|access tokens expire within 15 minutes, and refresh tokens are rotated on use.⟧

Authorization means checking what the caller may do.

## 6. Encryption in plain words

Encryption turns readable data into unreadable data, and only someone with the key can read it again. There are two situations. "At rest" is data stored on disk, "in transit" is data travelling over the network.

⟦F1|Data at rest is encrypted with KMS-managed keys.⟧

⟦S:CRYPTO-04|Traffic between services, and between services and data stores or brokers, is encrypted in transit.⟧ ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧ ⟦S:CRYPTO-07|Services validate TLS certificates and never disable verification.⟧

## 7. Secrets

A secret is anything that gives access, such as a password or a key. ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧

## 8. Personal data

The decisions contain personal data such as email and phone number. ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧ ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧

## 9. Network

⟦S:NET-04|Services that call third parties have their egress restricted to an approved allowlist.⟧

We also run failover tests, where we switch to the standby database and check that scoring continues. To keep those tests simple, ⟦F2|the database is reachable from outside the VPC, so the test runner can connect from a laptop.⟧ The test runner is only used by the Risk Engineering team.

## 10. Logging

⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧

## 11. Callbacks and queries

When a decision is "block", the service calls back the payments team. ⟦S:API-03|Webhook payloads, outbound and inbound, are signed, and the signatures are verified.⟧ ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧

## 12. Building and running

⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧ ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧

## 13. How the decision is made

The engine first applies simple rules, such as "the same device used in three countries in one hour". If a rule says block, the decision is made without the model. Otherwise the model produces a score between 0 and 1 and the thresholds map it to allow, review or block. The reasons are a short list of the rules or features that influenced the score, and they are stored together with the decision so analysts can understand it.

The engine is stateless. All counters come from the payment event itself, which means we can run several copies of the engine at the same time and Kafka will divide the events between them.

## 14. Open questions

- What should happen when the model service is slow? Sanjana suggests falling back to rules only.
- Should analysts be able to override a decision, and who would approve that?
