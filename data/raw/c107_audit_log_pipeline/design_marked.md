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
- ⟦S:AUTH-02|Internal service calls are authenticated with mutual TLS or signed workload identity tokens.⟧
- ⟦S:AUTHZ-02|Internal users receive only the roles required for their job, and roles are defined per service.⟧
- ⟦S:AUTHZ-05|Access rights to production systems are reviewed at least quarterly.⟧
- ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧
- ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
- ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧
- ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧
- ⟦S:NET-02|The audit archive blocks public access and is private by default.⟧
- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧
- ⟦S:LOG-04|Access to centralized logs is limited to authorized staff.⟧
- ⟦S:DATA-01|Only the personal data needed for the purpose is collected and stored.⟧
- ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧
- ⟦S:DATA-05|Data exports require authorization, are encrypted, and expire after a limited time.⟧
- ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧

todo: sizing sheet, see old wiki page "audit hub" (dead link)
