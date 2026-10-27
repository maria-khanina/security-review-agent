# Fraud Scoring Service - Design Document

Author: Pawel S., Risk Engineering
Status: For review

## 1. Introduction

The Fraud Scoring Service evaluate every payment in the near real time and write a decision: allow, review or block. It replace the nightly batch job. The service read the payment events from the MSK topic, apply the rules and the model, and store the result.

## 2. Components

- **payment-events (MSK)** - input topic, one event for every payment with the customer attributes.
- **scoring-engine** - the service which read the events, calculate the score and write the decision.
- **decisions-db (PostgreSQL)** - store the risk decisions.
- **scoring audit log group** - the place in CloudWatch where audit records are written.

The infrastructure is created with Terraform. There are six resources: the KMS key `scoring_key`, the MSK cluster `payment_events`, the database `decisions_db`, the security group `decisions_sg`, the log group `scoring_audit` and the IAM policy `scoring_policy`.

## 3. Data flow

First, payment-events send the payment event to the scoring-engine. Second, the scoring-engine write the risk decision to decisions-db. Third, the scoring-engine write an audit record to the scoring audit log group. There is no other data flow.

## 4. Access control

Calls to the scoring-engine from the other internal services are authenticated with mutual TLS or signed workload identity tokens. The access tokens expire in 15 minutes at maximum, and the refresh tokens are rotated on every use.

## 5. Data protection

Personal data in our databases and object storage is encrypted at rest with AES-256, using keys held in the corporate key management service. The encryption keys are held in KMS, never stored with the data which they protect, and rotated at least annually.

Reports and exports with personal data are available only to authorized users, stored encrypted, and deleted after 7 days.

The traffic between services, and between services and data stores or brokers, is encrypted in transit. The services validate the TLS certificates and never disable the verification. We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.

Only the support engineers of this service and the security analysts can read the central logs, because they use them to resolve customer tickets and to review security events; nobody else has access.

We scrub logs so that they contain neither secrets, card numbers nor personal data other than opaque identifiers.

 Data goes to the processor under the signed data processing agreement and only the fields it needs for the contracted task are sent: the order reference and the delivery address, because nothing else is required for delivery.
 Audit logs are tamper-evident and kept for at least a year.

## 6. Secrets

No secrets are kept in source code, config files, API specs or infrastructure definitions. The runtime secrets are fetched from the approved secret store when the service start.

We keep personal data for 12 months at most and delete it automatically when the period ends, or earlier on a verified request.

## 7. Network

The database and the message brokers are in the private subnets and are not publicly reachable. Outbound firewall rules are managed by each team and are rarely reviewed.

The database account of the service has the minimum grants its functions need: reads on two tables and writes on one, and the administrative credentials are held by the database team alone.

## 8. Callbacks

When the decision is block, the service call back the payments team and also receive the callbacks from the partner sandbox during the integration tests. The signature verification is skipped for the callbacks from the partner sandbox. The reason is that the sandbox of the partner is not able to sign the messages yet.

The service stores only the personal fields that appear in its data inventory with a stated purpose.

## 9. Logging

The audit trail includes authentication failures, privilege changes and sensitive-data access.
Service credentials must be rotated at least every 90 days and immediately after suspected exposure.

## 10. Application and operations

User input reaches the database only as query parameters, never as part of the query text. The CI scan the dependencies and images, and the critical vulnerabilities are fixed within 14 days. No container runs as root, and the root filesystem is read-only wherever possible.

Nothing administrative or meant for debugging can be called from outside our network.

## 11. Storage and testing

The decisions-db (PostgreSQL) is the only datastore which the engine writes to, and it runs as a primary with a standby in the second availability zone. The engine is tested in the test environment with the usual functional tests. The scoring-engine is exercised in the test environment by the functional test suite.

## 12. How the decision is made

The engine first apply the simple rules, for example the same device used in three countries in one hour. If a rule say block, the decision is made without the model. Otherwise the model give a score between 0 and 1 and the thresholds map it to allow, review or block. The reasons, a short list of the rules or features which influenced the score, are stored with the decision so the analysts can understand it.

The engine is stateless. All the counters come from the payment event itself, so we can run several copies of the engine, and Kafka divide the events between them.

## 13. Open points

- The alert thresholds for the consumer lag are not decided.
- The name of the mailbox for the review queue.
