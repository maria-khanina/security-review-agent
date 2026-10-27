# Fraud Scoring: stories and design

Epic: RISK-300 (Real-time scoring)
Status: In development

## Overview

Real-time scoring replaces the nightly batch. payment-events (MSK) delivers one event per payment to the scoring-engine, which writes a decision to decisions-db (PostgreSQL) and an audit record to the scoring audit log group. The infrastructure is declared in Terraform: `scoring_key` (KMS), `payment_events` (MSK), `decisions_db` (RDS), `decisions_sg` (security group), `scoring_audit` (log group) and `scoring_policy` (IAM).

## Stories

### RISK-301: Score every payment

As a risk analyst, I want every payment scored within seconds so that suspicious payments are reviewed early.

Acceptance criteria:
- Each event produces exactly one decision (allow, review or block) with a score and reasons.
- A rule that says block ends the decision without the model.
- Decisions are stored with the customer attributes that were scored.

### RISK-302: Review queue

As a fraud analyst, I want the review decisions delivered in a morning queue.

Acceptance criteria:
- Decisions of type review are collected and delivered to the analyst mailbox each morning.
- The analyst's conclusion is stored alongside the decision and does not change the stored score.
- The analyst can export the filtered list to CSV.

### RISK-303: Shadow mode for new models

As a model owner, I want to run a new model in shadow mode so that I can compare it with the active one.

Acceptance criteria:
- A shadow model scores every event but its decisions have no effect.
- The disagreement rate with the active model is reported daily.

## Design decisions

1. The service role can only read its own table.
2. Logging: ⟦F1|only HTTP access logs from the load balancer in front of the review console are kept.⟧

⟦S:LOG-02|Log lines are kept free of secrets, card numbers and personal details, and identifiers are opaque.⟧

⟦S:CRYPTO-04|In-transit encryption covers calls between services as well as connections to databases and queues.⟧
⟦S:OPS-03|Backups must be encrypted and restoration must be tested at least twice a year.⟧
⟦S:OPS-01|CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.⟧

## Non-functional requirements

| Area | Requirement |
|---|---|
| Service authentication | ⟦S:AUTH-02|Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.⟧ |
| Encryption at rest | ⟦S:CRYPTO-01|The databases and object stores that hold PII use AES-256 encryption at rest.⟧ |
| Algorithms | ⟦S:CRYPTO-05|Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.⟧ |
| Secrets in artifacts | ⟦S:SECRET-01|Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.⟧ |
| Network | ⟦S:NET-01|decisions-db and the MSK brokers sit in private subnets and are not publicly reachable.⟧ |
| Log access | ⟦S:LOG-04|The central logs are readable by the platform operators, who need them to keep the service running, and by the auditors, who need them for their yearly review; all other roles are denied.⟧ |
| Minimization | ⟦S:DATA-01|The data inventory of the service lists every stored personal field with its purpose, and a field without a listed purpose is not collected.⟧ |
| Third parties | ⟦S:DATA-03|Third parties receive only the fields they need, and only if an approved data processing agreement covers them.⟧ |
| Exports | ⟦S:DATA-05|Each export file is encrypted at rest, readable only by the authorized requester, and removed automatically after 72 hours.⟧ |
| Queries | ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧ |

⟦S:AUTHZ-02|The service defines three roles of its own: operator, auditor and administrator; operators need write access to run the daily jobs, auditors only read, and administrators are limited to the platform team.⟧
⟦S:SECRET-02|The approved secret manager is the only source of runtime secrets, fetched at start-up.⟧
⟦S:DATA-02|We keep personal data for 12 months at most and delete it automatically when the period ends, or earlier on a verified request.⟧
⟦F2|There is no periodic review of who has production access.⟧

## Design notes

The engine is stateless: all counters come from the payment event, so several copies can run in parallel and Kafka splits the events between them. The number of topic partitions caps the parallelism; the initial setting is enough for the expected volume. Consumer lag is monitored. A model update is deployed separately from the engine, runs in shadow mode first, and is promoted only if the disagreement rate is within agreed bounds. Rolling back to the previous model is a configuration change.

## Definition of done

- Acceptance criteria demonstrated in staging.
- Dashboard for consumer lag and decision rates exists.
- Alert threshold for lag agreed with Operations (TBD).
- Name of the review queue mailbox decided (TBD).
