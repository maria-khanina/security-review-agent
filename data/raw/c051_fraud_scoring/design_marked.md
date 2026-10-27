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

⟦S:AUTH-02|Calls to the scoring-engine from the other internal services are authenticated with mutual TLS or signed workload identity tokens.⟧ ⟦S:AUTH-03|The access tokens expire in 15 minutes at maximum, and the refresh tokens are rotated on every use.⟧

## 5. Data protection

⟦S:CRYPTO-01|Personal data in our databases and object storage is encrypted at rest with AES-256, using keys held in the corporate key management service.⟧ ⟦S:CRYPTO-06|The encryption keys are held in KMS, never stored with the data which they protect, and rotated at least annually.⟧

⟦S:DATA-05|Reports and exports with personal data are available only to authorized users, stored encrypted, and deleted after 7 days.⟧

⟦S:CRYPTO-04|The traffic between services, and between services and data stores or brokers, is encrypted in transit.⟧ ⟦S:CRYPTO-07|The services validate the TLS certificates and never disable the verification.⟧ ⟦S:CRYPTO-05|We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.⟧

⟦S:LOG-04|Only the support engineers of this service and the security analysts can read the central logs, because they use them to resolve customer tickets and to review security events; nobody else has access.⟧

⟦S:LOG-02|We scrub logs so that they contain neither secrets, card numbers nor personal data other than opaque identifiers.⟧

 ⟦S:DATA-03|Data goes to the processor under the signed data processing agreement and only the fields it needs for the contracted task are sent: the order reference and the delivery address, because nothing else is required for delivery.⟧
 ⟦S:LOG-03|Audit logs are tamper-evident and kept for at least a year.⟧

## 6. Secrets

⟦S:SECRET-01|No secrets are kept in source code, config files, API specs or infrastructure definitions.⟧ ⟦S:SECRET-02|The runtime secrets are fetched from the approved secret store when the service start.⟧

⟦S:DATA-02|We keep personal data for 12 months at most and delete it automatically when the period ends, or earlier on a verified request.⟧

## 7. Network

⟦S:NET-01|The database and the message brokers are in the private subnets and are not publicly reachable.⟧ ⟦F4|Outbound firewall rules are managed by each team and are rarely reviewed.⟧

⟦S:AUTHZ-03|The database account of the service has the minimum grants its functions need: reads on two tables and writes on one, and the administrative credentials are held by the database team alone.⟧

## 8. Callbacks

When the decision is block, the service call back the payments team and also receive the callbacks from the partner sandbox during the integration tests. ⟦F3|The signature verification is skipped for the callbacks from the partner sandbox.⟧ The reason is that the sandbox of the partner is not able to sign the messages yet.

⟦S:DATA-01|The service stores only the personal fields that appear in its data inventory with a stated purpose.⟧

## 9. Logging

⟦S:LOG-01|The audit trail includes authentication failures, privilege changes and sensitive-data access.⟧
⟦S:SECRET-03|Service credentials must be rotated at least every 90 days and immediately after suspected exposure.⟧

## 10. Application and operations

⟦S:API-05|User input reaches the database only as query parameters, never as part of the query text.⟧ ⟦S:OPS-01|The CI scan the dependencies and images, and the critical vulnerabilities are fixed within 14 days.⟧ ⟦S:OPS-02|No container runs as root, and the root filesystem is read-only wherever possible.⟧

⟦S:AUTHZ-04|Nothing administrative or meant for debugging can be called from outside our network.⟧

## 11. Storage and testing

⟦F1|The decisions-db (PostgreSQL) is the only datastore which the engine writes to, and it runs as a primary with a standby in the second availability zone.⟧ The engine is tested in the test environment with the usual functional tests. ⟦F2|The scoring-engine is exercised in the test environment by the functional test suite.⟧

## 12. How the decision is made

The engine first apply the simple rules, for example the same device used in three countries in one hour. If a rule say block, the decision is made without the model. Otherwise the model give a score between 0 and 1 and the thresholds map it to allow, review or block. The reasons, a short list of the rules or features which influenced the score, are stored with the decision so the analysts can understand it.

The engine is stateless. All the counters come from the payment event itself, so we can run several copies of the engine, and Kafka divide the events between them.

## 13. Open points

- The alert thresholds for the consumer lag are not decided.
- The name of the mailbox for the review queue.
