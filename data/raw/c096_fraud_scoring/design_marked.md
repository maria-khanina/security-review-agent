# fraud scoring - design

old page: wiki/fraud-batch (link dead, ask Pavel)

## what

- events from payment-events (MSK) -> scoring-engine -> decision to decisions-db, audit record to log group
- decision = allow / review / block + score + reasons
- stateless engine, counters come from the event

## tf

- kms scoring_key
- msk payment_events
- rds decisions_db
- sg decisions_sg
- loggroup scoring_audit
- iam scoring_policy

## db

- ⟦F1|The database accepts connections only from the application subnet.⟧
- ⟦S:CRYPTO-01|PII at rest is AES-256.⟧
- ⟦S:API-05|Parameterized queries only.⟧
- ⟦S:DATA-01|Only personal data needed for scoring is stored.⟧

## third party

- ⟦F2|Device signals are bought from a vendor and the customer's device id and email are sent to them under a verbal agreement with their account manager.⟧

## access

- ⟦S:AUTH-02|Internal service calls to the scoring-engine use mTLS or signed workload identity tokens.⟧
- ⟦S:AUTHZ-02|Internal users get only the roles their job requires; roles are defined per service.⟧
- ⟦S:AUTHZ-05|Production access is reviewed at least quarterly.⟧

## crypto / secrets

- ⟦S:CRYPTO-05|Approved algorithms only; MD5, SHA-1, DES, 3DES and ECB are prohibited.⟧
- ⟦S:SECRET-01|No secrets in code, config, specs or infra definitions.⟧

## logs

- ⟦F3|scoring-engine writes a log line for every event it processes.⟧
- ⟦S:LOG-01|Auth failures, privilege changes and access to sensitive data are logged.⟧
- ⟦S:LOG-04|Log access limited to authorized staff.⟧

## exports

- ⟦S:DATA-05|Exports with personal data (analyst CSV) need authorization, are encrypted in storage and expire.⟧

