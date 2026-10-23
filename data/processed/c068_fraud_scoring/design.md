# Fraud Scoring: A Guided Design (for new joiners)

Author: Lukas, Risk Engineering (junior)
Reviewer: Sanjana

## 1. The problem in plain words

Every time a customer pays, someone has to decide if the payment looks suspicious. A fraud score is a number that tells how risky a payment is. If the number is small we allow the payment, if it is in the middle a human looks at it, and if it is big we block it. This service calculates that number and remembers the decision.

## 2. The pieces

- **payment-events (MSK).** MSK is managed Kafka. Think of Kafka as a conveyor belt: services put messages on it, other services take them off. Each payment puts an event on the belt.
- **scoring-engine.** It reads each event, applies the rules and the model and makes a decision.
- **decisions-db (PostgreSQL).** The engine writes every decision here, together with the customer attributes it used.
- **scoring audit log group.** A place in CloudWatch where the engine writes an audit record for each decision.

## 3. The path of one payment

There are only three arrows. First, payment-events delivers the event to the scoring-engine. Second, the scoring-engine writes the risk decision to decisions-db. Third, the scoring-engine writes an audit record to the scoring audit log group. I drew it three times on paper before I understood it, so please read this section twice.

## 4. The infrastructure

Everything is created with Terraform, which means the infrastructure is described in files, not clicked together by hand. The files declare six resources: a KMS key (`scoring_key`) for encryption, the MSK cluster (`payment_events`), the PostgreSQL database (`decisions_db`), a security group (`decisions_sg`) that works like a firewall for the database, the log group (`scoring_audit`) and an IAM policy (`scoring_policy`) that says what the engine may do inside AWS.

## 5. Who may call whom?

Authentication means checking who is calling. Internal service calls to the scoring-engine are authenticated with mutual TLS or signed workload identity tokens. A token is a small signed piece of text. Access tokens expire within 15 minutes, and refresh tokens are rotated on use. Rotation means a new refresh token is given every time the old one is used.

Authorization means checking what the caller may do.

## 6. Encryption, explained

Encryption makes data unreadable for anyone without the key. We use it in two situations, "at rest" (data stored on a disk) and "in transit" (data moving on the network).

Personally identifiable information is encrypted at rest with AES-256. Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually. Traffic between services, and between services and data stores or brokers, is encrypted in transit. Services validate TLS certificates and never disable verification. Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.

## 7. Secrets

A secret is anything that gives access, for example a password or a key. Secrets do not appear in source code, configuration files, specifications or infrastructure definitions. Runtime secrets are fetched from the approved secret store at startup.

## 8. Network

decisions-db and the MSK brokers sit in private subnets and are not publicly reachable. Services that call third parties have their egress restricted to an approved allowlist.

## 9. Personal data

The decisions contain personal data such as email and phone. Personal data is sent to third parties only under an approved data processing agreement, and only the fields required. Non-production environments do not contain real personal or card data.

## 10. Logging

Logs are the diary of the system. Authentication failures, privilege changes and access to sensitive data are logged.

## 11. Callbacks and queries

When a decision is "block", the service calls back the payments team. Webhook payloads, outbound and inbound, are signed, and the signatures are verified. A signature is like a wax seal on a letter. Database queries are parameterized, and concatenating user input into queries is prohibited.

## 12. Build and run

The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days. Containers run as a non-root user, with a read-only root filesystem where possible.

## 13. How the decision is made

First the engine checks simple rules, for example the same device used in three countries in one hour. If a rule says block, the decision is made without the model. Otherwise the model gives a number between 0 and 1 and thresholds map it to allow, review or block. The reasons are a short list of rules or features that influenced the number, and they are stored with the decision so that analysts can understand it.

The engine does not remember anything between events. All counters come from the event itself, so we can run many copies of the engine at the same time, and Kafka splits the events between them. This is called being stateless, and it makes scaling easy.

## 14. Questions for the review

- What should the engine do when the model is slow? Sanjana suggests using rules only for a while.
- Who is allowed to override a decision, and who approves that? (see the old thread in the risk channel, link may not open)
