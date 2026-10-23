fraud scoring - quick notes

- scoring-engine reads payment events from payment-events (MSK), scores them, writes decision to decisions-db (PostgreSQL)
- audit records go to scoring audit log group
- terraform: scoring_key, payment_events, decisions_db, decisions_sg, scoring_audit, scoring_policy
- scoring-engine runs as several copies, and every copy reads its own partitions of payment-events (MSK) and writes decisions to decisions-db (PostgreSQL).
- decision = score + reasons + event id, written once per event
- peak ~800 events/s, decision within 100ms median
- engine is stateless, counters come from the event itself

security stuff:
- The service image keeps the default root user, because changing it broke file access.
- Internal calls are authenticated only by a shared header value that all services know.
- Personally identifiable information is encrypted at rest with AES-256.
- Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- Runtime secrets are fetched from the approved secret store at startup.
- Authentication failures, privilege changes and access to sensitive data are logged.
- Logs contain no secrets, card numbers or personal data beyond opaque identifiers.
- Personal data has a defined retention period and is deleted when it expires or on a verified request from the data subject.
- Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.
- Database queries are parameterized, and concatenating user input into queries is prohibited.
- The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.

todo: replay tool for old events (TBD), alert on score drift (TBD)
