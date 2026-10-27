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

Authentication means checking who is calling. ⟦S:AUTH-02|We do not trust the internal network by itself: every internal call is authenticated with mTLS or workload identity tokens.⟧ A token is a small signed piece of text. ⟦S:AUTH-03|Tokens are short-lived (15 minutes maximum) and refresh tokens are single-use, so each refresh issues a new one.⟧ Rotation means a new refresh token is given every time the old one is used.

⟦S:AUTHZ-04|Debug and administrative routes are not exposed to the internet.⟧

Authorization means checking what the caller may do.

## 6. Encryption, explained

Encryption makes data unreadable for anyone without the key. We use it in two situations, "at rest" (data stored on a disk) and "in transit" (data moving on the network).

⟦S:CRYPTO-01|Personal data in our databases and object storage is encrypted at rest with AES-256, using keys held in the corporate key management service.⟧ ⟦S:CRYPTO-06|Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year.⟧ ⟦S:CRYPTO-04|Traffic between services, and between services and data stores or brokers, is encrypted in transit.⟧ ⟦S:CRYPTO-07|Clients check the certificate chain and host name on every TLS connection and have no insecure mode.⟧ ⟦S:CRYPTO-05|Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.⟧

⟦S:OPS-03|Encrypted backups are checked by a restoration exercise at least twice a year.⟧

⟦S:AUTHZ-03|The service connects with its own database account that has only SELECT and INSERT on the tables it uses, because it never updates or deletes rows; no administrative account is shared with other services.⟧
⟦S:LOG-04|Access to the central logs is limited to the on-call engineers of the owning team, who need it to investigate incidents, and to the security analysts, who need it to review audit events.⟧

## 7. Secrets

A secret is anything that gives access, for example a password or a key. ⟦S:SECRET-01|No secrets are kept in source code, config files, API specs or infrastructure definitions.⟧ ⟦S:SECRET-02|Runtime secrets are read from the secret store when the service starts.⟧

## 8. Network

⟦S:NET-01|decisions-db and the MSK brokers sit in private subnets and are not publicly reachable.⟧ ⟦S:NET-04|Services that call third parties have their egress restricted to an approved allowlist.⟧

⟦S:SECRET-03|We rotate service credentials at least every 90 days and straight away after any suspected exposure.⟧

## 9. Personal data

The decisions contain personal data such as email and phone. ⟦S:DATA-03|Before sending data to a partner we check the data processing agreement and strip every field that the partner does not need for its task, so only the agreed fields leave the platform.⟧ ⟦S:DATA-04|Only synthetic data is present outside production.⟧

## 10. Logging

Logs are the diary of the system. ⟦S:LOG-01|We log failed logins, changes of privileges and reads of sensitive data.⟧

⟦S:LOG-02|We scrub logs so that they contain neither secrets, card numbers nor personal data other than opaque identifiers.⟧

## 11. Callbacks and queries

When a decision is "block", the service calls back the payments team. ⟦S:API-03|Every webhook we send or receive is signed with an HMAC, and the receiver checks the signature together with the timestamp.⟧ A signature is like a wax seal on a letter. ⟦S:API-05|Database queries are parameterized, and user input is never concatenated into SQL.⟧

## 12. Build and run

⟦S:OPS-01|CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧ ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧

⟦S:DATA-01|Each personal field we store is documented in the data inventory together with its purpose, and fields with no purpose are dropped.⟧

## 13. How the decision is made

First the engine checks simple rules, for example the same device used in three countries in one hour. If a rule says block, the decision is made without the model. Otherwise the model gives a number between 0 and 1 and thresholds map it to allow, review or block. The reasons are a short list of rules or features that influenced the number, and they are stored with the decision so that analysts can understand it.

The engine does not remember anything between events. All counters come from the event itself, so we can run many copies of the engine at the same time, and Kafka splits the events between them. This is called being stateless, and it makes scaling easy.

## 14. Questions for the review

- What should the engine do when the model is slow? Sanjana suggests using rules only for a while.
- Who is allowed to override a decision, and who approves that? (see the old thread in the risk channel, link may not open)
