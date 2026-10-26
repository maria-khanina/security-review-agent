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

Authentication means checking who the caller is. ⟦S:AUTH-02|Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.⟧ When tokens are used, ⟦S:AUTH-03|access tokens expire within 15 minutes, and refresh tokens are rotated on use.⟧

⟦S:SECRET-03|Rotation of service credentials happens every 90 days or sooner, and immediately after suspected exposure.⟧

Authorization means checking what the caller may do.

## 6. Encryption in plain words

Encryption turns readable data into unreadable data, and only someone with the key can read it again. There are two situations. "At rest" is data stored on disk, "in transit" is data travelling over the network.

Data at rest is encrypted with KMS-managed keys.

⟦S:CRYPTO-04|Traffic between services, and between services and data stores or brokers, is encrypted in transit.⟧ ⟦S:CRYPTO-05|We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.⟧ ⟦S:CRYPTO-07|Outbound TLS connections always verify the peer certificate.⟧

⟦S:LOG-03|Audit logs are tamper-evident and kept for at least a year.⟧

⟦S:LOG-02|Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.⟧

⟦S:AUTHZ-03|The service connects to its database with its own account, which has only the grants it needs.⟧

## 7. Secrets

A secret is anything that gives access, such as a password or a key. ⟦S:SECRET-01|Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.⟧ ⟦S:SECRET-02|At startup the service fetches its secrets from the approved secret store.⟧

⟦S:CRYPTO-01|Personal data in our databases and object storage is encrypted at rest with AES-256, using keys held in the corporate key management service.⟧

## 8. Personal data

The decisions contain personal data such as email and phone number. ⟦S:DATA-03|Before personal data is shared with a third party, an approved DPA must be in place, and we send just the fields needed.⟧ ⟦S:DATA-04|Real customer and card data is kept out of dev, test and staging.⟧

⟦S:AUTHZ-02|Staff roles are limited to what each job needs, and every service defines its own roles.⟧

⟦S:CRYPTO-06|Keys are managed in KMS, never stored next to the encrypted data, and rotated annually.⟧

⟦S:AUTHZ-04|Debug and administrative routes are not exposed to the internet.⟧

## 9. Network

⟦S:NET-04|Third-party calls leave through an egress allowlist, not through open outbound access.⟧
⟦S:LOG-04|Reading centralized logs requires authorization, and only approved staff have it.⟧

We also run failover tests, where we switch to the standby database and check that scoring continues. To keep those tests simple, ⟦F1|the database is reachable from outside the VPC, so the test runner can connect from a laptop.⟧ The test runner is only used by the Risk Engineering team.

## 10. Logging

⟦S:LOG-01|Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.⟧

## 11. Callbacks and queries

When a decision is "block", the service calls back the payments team. ⟦S:API-03|Webhook payloads are HMAC-signed and timestamped, and the receiver verifies the signature and the timestamp before accepting them.⟧ ⟦S:API-05|All queries use bound parameters instead of string concatenation.⟧

⟦S:OPS-03|Backups must be encrypted and restoration must be tested at least twice a year.⟧

## 12. Building and running

⟦S:OPS-01|Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less.⟧ ⟦S:OPS-02|No container runs as root, and the root filesystem is read-only wherever possible.⟧

## 13. How the decision is made

The engine first applies simple rules, such as "the same device used in three countries in one hour". If a rule says block, the decision is made without the model. Otherwise the model produces a score between 0 and 1 and the thresholds map it to allow, review or block. The reasons are a short list of the rules or features that influenced the score, and they are stored together with the decision so analysts can understand it.

The engine is stateless. All counters come from the payment event itself, which means we can run several copies of the engine at the same time and Kafka will divide the events between them.

## 14. Open questions

- What should happen when the model service is slow? Sanjana suggests falling back to rules only.
- Should analysts be able to override a decision, and who would approve that?
