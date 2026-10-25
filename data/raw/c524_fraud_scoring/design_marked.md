# Fraud Scoring Service - A Beginner-Friendly Design

## 1. Background and goals

Every day Meridian Pay processes many card payments, and a small number of them are fraud. Fraud means that somebody uses a card or an account that does not belong to them. The Fraud Scoring Service looks at every payment, gives it a risk score between 0 and 100 and writes a decision: allow, review or block. In this document we explain the parts of the service step by step, because new team members often ask what a "score" or an "event" is.

An **event** is a small message that says that something happened, for example "payment 123 was created". A **score** is a number that says how risky the event is. A **decision** is the action that follows from the score.

## 2. Non-goals

The service does not move money, it does not talk to customers and it does not learn new models by itself. The training of the models is done by the data science team in their own environment.

## 3. Parts of the system

- **scoring-engine** is the main program. It reads events, computes the score and writes the decision.
- **payment-events (MSK)** is the stream of payment events. MSK is the managed Kafka of the cloud provider; Kafka is a system that keeps messages in order, so that readers can take them one after another.
- **decisions-db (PostgreSQL)** is the database in which the decisions are stored. PostgreSQL is a relational database, which means that data is kept in tables with rows and columns.
- **scoring audit log group** receives one audit record for every decision.

## 4. How a payment is scored

1. The payment service creates a payment and publishes the event to payment-events. The event has the payment id, the amount, the currency, the merchant and attributes of the customer such as the country and the age of the account.
2. scoring-engine reads the event, adds the history of the customer from decisions-db and computes the features of the model. A **feature** is one number that the model uses, for example "number of payments in the last hour".
3. The model returns the score. The rules after the model turn the score into a decision.
4. scoring-engine writes the decision to decisions-db with the payment id, the score, the decision, the version of the model and the time.
5. An audit record goes to the audit log group.

The payment service reads the decision from decisions-db before it completes the payment. The decision is therefore available a few hundred milliseconds after the event.

## 5. Data model

The table `decisions` has the columns payment_id, customer_id, score, decision, model_version and decided_at. The table `customer_history` has customer_id, the count of payments per day and the average amount. Both tables belong to decisions-db.

## 6. Reports for analysts

The analysts of the risk team want to understand why many payments were blocked. ⟦F1|Every night the analytics jobs copy the decisions together with the customer attributes to a cloud region outside the EU, where the compute is cheaper, and process them there.⟧ The results are tables with the share of blocked payments per country and per merchant.

## 7. Operation

### 7.1 Delivery

The service is built from the repository `fraud-scoring` by the pipeline of the platform team. The release goes to production after the tests have passed.

### 7.2 Changes

⟦S:CHG-02|Every change to production has a rollback plan that has been tested in a pre-production environment.⟧ A change to the model is a change to production as well.

### 7.3 Data copies

⟦S:RES-02|Backups and replicas of the personal data of customers in the EU stay in regions of the EU as well.⟧ The read replica of decisions-db that serves the dashboards is in the same region as the primary.

### 7.4 Dashboards

The dashboards show the latency of scoring, the number of events per second and the lag of the consumer. ⟦F2|scoring-engine exposes traces and metrics for the dashboards of the platform team.⟧ A consumer is a program that reads from the stream, and its **lag** is the number of events that are waiting.

## 8. Failure modes and retries

If scoring-engine is slow, the payment service waits for at most two seconds and then continues with the decision `review`. If decisions-db is not reachable, scoring-engine keeps the events in the stream and does not commit its position, so that the events are read again after the database is back. A commit here means that the consumer tells the stream that it has processed the events up to a certain place.

If the model returns an error, the rules use a default score of 50, and the decision is `review`.

## 9. Rollout plan

The service starts in shadow mode for two weeks: it computes scores, but the payment service ignores them. Then it blocks the payments with a score above 90, and after another two weeks it uses the full rules.

## 10. Open questions

- Should the decisions of the last 90 days be shown to the support agents?
- Which model version is the baseline for the comparison in shadow mode?
