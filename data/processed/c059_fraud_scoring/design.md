# Fraud Scoring Service: Design and Compliance Statement

Document owner: Risk Compliance
Version: 1.1 (reviewed by Security Architecture)

## 1. Purpose and Scope

This document describes the design of the Fraud Scoring Service ("the Service") and records, for each applicable requirement of the Meridian Pay Information Security Policy, the control by which the Service satisfies that requirement. It applies to the production environment and to the environments that support it. The Service evaluates every payment event in near real time and writes a decision of allow, review or block.

## 2. Functional Description

The Service consists of the following components:

- payment-events (MSK), the input topic carrying one event per payment together with customer attributes;
- scoring-engine, the service that reads each event, applies rules and a model, and produces a decision;
- decisions-db (PostgreSQL), the datastore for decisions and the customer attributes that were scored;
- the scoring audit log group, which receives an audit record for each decision.

The infrastructure is declared in Terraform. It consists of the KMS key `scoring_key`, the MSK cluster `payment_events`, the database instance `decisions_db`, the security group `decisions_sg`, the log group `scoring_audit` and the IAM policy `scoring_policy`.

### 2.1 Processing

For each event the scoring-engine first applies deterministic rules, for example rules that detect a device used in several countries within a short period. If a rule yields a block decision, the decision is final. Otherwise the engine computes a model score between zero and one and maps it to allow, review or block using configured thresholds. The reasons for the decision are a short list of the rules or features that influenced it, and they are stored together with the decision.

### 2.2 Review handling

Decisions of type review are collected into a queue that is delivered to the fraud analysts every morning. Analysts record their conclusion, and the conclusion is stored alongside the original decision. The conclusion does not alter the stored model score. This separation allows the model to be evaluated against analyst conclusions over time.

## 3. Controls

3.1 In accordance with policy,

3.2 Personally identifiable information held in decisions-db is encrypted at rest with AES-256.

3.3 Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.

3.4 No secrets are kept in source code, config files, API specs or infrastructure definitions.

3.5 Runtime secrets are fetched from the approved secret store when the Service starts.

3.7 The audit trail includes authentication failures, privilege changes and sensitive-data access.

3.8 Log lines are kept free of secrets, card numbers and personal details, and identifiers are opaque.

3.9 Each category of personal data has a defined retention period, and a scheduled job deletes the data when the period ends or upon a verified request from the data subject.

3.10 Third parties receive only the fields they need, and only if an approved data processing agreement covers them.

3.11 All queries use bound parameters instead of string concatenation.

3.12 The continuous integration pipeline scans dependencies and container images, and critical vulnerabilities are fixed within 14 days.

## 4. Operational Characteristics

The Service is stateless: all counters used by the rules are carried in the payment event, so several instances of the scoring-engine may run concurrently and Kafka divides the events between them. The number of partitions of the input topic caps the degree of parallelism; the initial setting is sufficient for the expected volume and may be raised before seasonal peaks. Consumer lag is monitored, and an alert fires when the lag exceeds a threshold that is defined in the operations runbook.

Model updates are deployed separately from the engine. A new model version first runs in shadow mode, where it scores every event but its decisions are recorded without effect. Its decisions are compared with those of the active model for a defined period, and the new version is promoted only if the disagreement rate is within the agreed bounds. Rollback to the previous model version is a configuration change and takes effect for new events immediately.

## 5. Outstanding Items

- Alert threshold for consumer lag: value TBD with Operations.
- Final naming of the review queue mailbox: TBD with the fraud analyst team.
