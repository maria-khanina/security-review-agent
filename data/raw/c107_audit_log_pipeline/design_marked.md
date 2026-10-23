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
- ⟦S:AUTH-02|Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.⟧
- ⟦S:AUTHZ-02|We keep roles small and per service, so an internal user only receives what their job requires.⟧
- ⟦S:AUTHZ-05|Access to production is recertified at least once per quarter.⟧
- ⟦S:CRYPTO-01|Personal data is encrypted at rest with AES-256.⟧
- ⟦S:CRYPTO-05|The approved algorithm list is followed, and MD5, SHA-1, DES, 3DES and ECB mode are prohibited in this service.⟧
- ⟦S:SECRET-01|Secrets stay out of the repository: not in code, configuration, specs or infrastructure files.⟧
- ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧
- ⟦S:NET-02|The audit archive blocks public access and is private by default.⟧
- ⟦S:LOG-01|We log failed logins, changes of privileges and reads of sensitive data.⟧
- ⟦S:LOG-04|Reading centralized logs requires authorization, and only approved staff have it.⟧
- ⟦S:DATA-01|Only the personal data needed for the purpose is collected and stored.⟧
- ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧
- ⟦S:DATA-05|Data exports require authorization, are encrypted, and expire after a limited time.⟧
- ⟦S:API-05|We use parameterized queries only, with no SQL built from user input by string concatenation.⟧

todo: sizing sheet, see old wiki page "audit hub" (dead link)
