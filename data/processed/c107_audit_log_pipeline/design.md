audit log pipeline (quick notes)

- what: collects audit events from all platfrom services, stores them for security team
- audit-collector = the service, takes events by internal api, puts on audit-stream (MSK)
- audit-stream (MSK) -> writer -> audit archive (S3), hourly files
- pipeline log group = collector ops logs
- terraform: audit_key, audit_stream, audit_archive, pipeline_audit, audit_backups, pipeline_policy
- events: source, actor, action, object, result, time. actor is an id not a name
- peak ~3000 events/s, one event ~1KB
- if stream is down >2 min collector refuses new events, sender decides

security stuff:
- Internal service calls are authenticated with mutual TLS or signed workload identity tokens.
- Internal users receive only the roles required for their job, and roles are defined per service.
- Access rights to production systems are reviewed at least quarterly.
- Personally identifiable information is encrypted at rest with AES-256.
- Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- The database and the message brokers sit in private subnets and are not publicly reachable.
- The audit archive blocks public access and is private by default.
- Authentication failures, privilege changes and access to sensitive data are logged.
- Access to centralized logs is limited to authorized staff.
- Only the personal data needed for the purpose is collected and stored.
- Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.
- Data exports require authorization, are encrypted, and expire after a limited time.
- Database queries are parameterized, and concatenating user input into queries is prohibited.

todo: sizing sheet, see old wiki page "audit hub" (dead link)
