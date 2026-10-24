# fraud scoring v2 - design

## goal

- score every payment in near real time, write a decision (allow / review / block)
- replace the old rules batch job

## pieces

- payment-events topic (MSK) - input, one event per payment with customer attrs
- scoring-engine (a.k.a. scorer) - ⟦F4|scoring-engine consumes events from the topic, runs the model and writes the result.⟧
- decisions DB (Postgres on RDS) - ⟦F2|decisions-db keeps every decision together with the customer attributes that were scored.⟧
- audit log group in CloudWatch
- kms key for encryption, iam policy for the engine, sg for the db

## data

- in: payment id, amount, country, device id, customer email + phone, history counters
- out: decision, score, reasons
- ⟦S:DATA-03|Nothing goes to third parties; if that ever changes then only under an approved DPA and only the needed fields.⟧

## db access

- ⟦F3|All services that read decisions, the engine included, connect to decisions-db with the shared master user to keep setup simple.⟧
- The database is in private subnets and has no public endpoint.
- sg decisions_sg allows 5432 from the app subnet

## security

- ⟦S:CRYPTO-01|PII at rest is encrypted with AES-256 (RDS storage encryption, kms key scoring_key).⟧
- ⟦S:CRYPTO-05|Only approved algs, MD5 SHA-1 DES 3DES ECB are not allowed.⟧
- ⟦F5|The filters of the decision search are built by joining the strings sent by the analysts, since the ORM could not express them.⟧
- ⟦S:LOG-01|Auth failures, privilege changes and access to sensitive data get logged.⟧
- ⟦S:AUTHZ-04|Debug and administrative routes are not exposed to the internet.⟧
- ⟦S:CRYPTO-04|Traffic between services and to data stores must be encrypted in transit.⟧
- ⟦S:LOG-02|Logs have no secrets, card numbers or personal data, just opaque ids.⟧
- ⟦S:AUTH-02|Internal service calls must be authenticated with mutual TLS or signed workload identity tokens.⟧
- ⟦S:OPS-02|Containers must run as a non-root user with a read-only root filesystem where possible.⟧

## build

- ⟦S:OPS-01|CI scans deps and images, critical vulns are fixed in 14 days.⟧
- terraform in infra/fraud-scoring, plan on PR

## todo later

- model versioning
- shadow mode for the new model
