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
- All personally identifiable information is encrypted before it lands on disk, using AES-256.
- Debug and administrative routes are not exposed to the internet.
- The application never uses a shared administrative database login; it has a dedicated, minimally privileged account.
- We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.
- No secrets are kept in source code, config files, API specs or infrastructure definitions.
- At startup the service fetches its secrets from the approved secret store.
- We log failed logins, changes of privileges and reads of sensitive data.
- We scrub logs so that they contain neither secrets, card numbers nor personal data other than opaque identifiers.
- Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.
- Before personal data is shared with a third party, an approved DPA must be in place, and we send just the fields needed.
- Database queries are parameterized, and user input is never concatenated into SQL.
- Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks.

todo: replay tool for old events (TBD), alert on score drift (TBD)
