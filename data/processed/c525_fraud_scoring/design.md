# Fraud Scoring Service - Design

## 1. Background

The Fraud Scoring Service is the successor of the Risk Engine of the monolith. It scores payments in real time and writes a decision for each of them. The text of this document was prepared from the Risk Engine design, and the sections on the data flow and on operation were taken over from there with the names replaced.

## 2. Goals and non-goals

Goals: a score and a decision for every payment within a few hundred milliseconds, and an audit record for every decision. Non-goals: model training, the manual review queue and the communication with customers.

## 3. Components

| Component | Role |
|---|---|
| scoring-engine | Reads payment events, computes the score, writes the decision (called "risk-engine" in some older diagrams) |
| payment-events (MSK) | Stream of payment events |
| decisions-db (PostgreSQL) | Decisions and customer history |
| scoring audit log group | Audit records of the decisions |

## 4. Data flow

The payment service publishes an event to payment-events (MSK) for each new payment. scoring-engine reads the event, loads the history of the customer from decisions-db, computes the features, applies the model and the rules, and writes the decision to decisions-db. Each decision also produces an audit record in the audit log group. The Risk Engine stores the decision in the table `risk_decisions`; in the new service the table is called `decisions` (some sections below still use the old name).

## 5. Data location

Personal data of customers in the EU is stored and processed only in regions of the EU. Backups and replicas of the personal data of customers in the EU stay in regions of the EU as well. The primary database of the Risk Engine was in Frankfurt, and decisions-db is in Frankfurt as well.

## 6. Delivery

The pipeline of the platform team builds and deploys the service. Credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour.

The artifacts of the service are signed with the signing key of the platform. The signing key is available to every developer of the company, so that any developer can sign a hotfix. The version 1 of the signing procedure (a key file on the build server) is replaced by the version 2 (a key in the key store); the following sections still describe the version 1.

## 7. Change

Rollback is part of the release process of the service. The rollback is tested for scoring-engine, which is the main service, and is not tested for the nightly jobs of the service. The release of the model follows the same process as the release of the service.

## 8. Observability

The dashboards show the latency of the scoring, the number of events per second and the lag of the consumer. The Risk Engine dashboards are linked from the wiki page of the old service.

## 9. Failure modes

If scoring-engine is slow, the payment service waits for at most two seconds and continues with the decision `review`. If decisions-db is not reachable, the events stay in the stream, and the consumer reads them again after the database is back. If the model returns an error, the default score is 50.

## 10. Rollout

The service runs in shadow mode for two weeks. Then it blocks the payments with a score above 90. After two more weeks it uses the full rules, and the Risk Engine is switched off one month later.

## 11. Open questions

- Which model version is the baseline in shadow mode.
- Whether the audit records are exported to the data warehouse.
