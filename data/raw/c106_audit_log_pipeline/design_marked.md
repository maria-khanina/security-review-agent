# Audit Log Pipeline: Design Overview

Maintainers: platform team
Revision history: 0.1 (hub), 0.4 (collector), 0.7 (this text, merged with the "Event Gateway" notes; some parts are older)

## 1. What the pipeline does

The Audit Log Pipeline collects audit events from every Meridian Pay service and stores them for the security and compliance teams. An event says who did what to which object, when, and with which result. The pipeline is internal. Customers never see it and no customer data is shown to a third party. It replaces the older "Event Gateway" (sometimes called the "log hub" or simply "the gateway" in the teams' own documents; in this text these names mean the same system until the migration is done).

## 2. Background

The Event Gateway was built in 2021 for one use, the monthly review of administrator actions. Since then the number of sources grew from four to forty, the search cluster that held the events became the most expensive component of the platform account, and the answer time for a simple query went up from seconds to minutes. The new pipeline keeps recent events on a stream for a short time and moves everything to cheap object storage in hourly files. Queries on the archive are run by the security team's own tool.

## 3. Components

- **audit-collector** is a stateless service. It accepts events from the platform services through an internal API, validates the structure, adds the time of receipt and the name of the source, and writes the event to the stream.
- **audit-stream (MSK)** is the managed Kafka cluster. ⟦F1|audit-stream (MSK) is shared by the collector and the archive writer and receives about three thousand events a second at the peak.⟧
- **audit archive (S3)** is the bucket in which the archive writer stores hourly batches per source service.
- **pipeline log group** holds the operational logs of the collector.

Terraform creates `audit_key`, `audit_stream`, `audit_archive`, `pipeline_audit`, `audit_backups` and `pipeline_policy`.

## 4. Authentication, version note

The sending services authenticate to the collector with the scheme described in the Event Gateway notes, which uses a shared key per source service. The collector design (version 0.4) moved to signed workload tokens. It is not clear to the author of this merged text which of the two is still in force for each of the forty sources, because the migration of the sources is under way and the old section was kept for reference. This is a known gap in the document.

## 5. Behavior under load

The collector answers an event with an acknowledgement as soon as the event is on the stream. If the stream is unavailable for more than two minutes, the collector refuses new events and the sender decides what to do. The archive writer reads the stream in consumer groups per source service so that a slow source cannot hold back the others. A batch file is closed every hour or when it reaches two hundred megabytes, whichever comes first, and a manifest file lists the batches of each hour.

## 6. Data and events

An event has source, actor, action, object, result and time. The actor is an opaque identifier, never a name or an e-mail address. Free text fields are not allowed in events; the collector rejects an event whose action is not in the catalog of actions maintained by the security team.

## 7. Control statements

7.1 Cryptography. ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧ ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧

7.2 Transport. ⟦F2|TLS between the components was switched off during the load tests in the spring and it has not been switched on again.⟧

7.3 Secrets. ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧

7.4 Storage. ⟦S:NET-02|The audit archive blocks public access and is private by default.⟧

7.5 Logging. ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧ ⟦S:LOG-02|Logs contain no secrets, card numbers or personal data beyond opaque identifiers.⟧

7.6 Data. ⟦S:DATA-02|Personal data has a defined retention period and is deleted when it expires or on a verified request from the data subject.⟧ ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧

7.7 Application and delivery. ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧ ⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧

7.8 Backups. ⟦F3|Backups of the archive are encrypted.⟧

## 8. Migration

Sources are moved in groups of five. A group is considered done when the old gateway has received no events from it for fourteen days. The old gateway is switched off when all groups are done. During the migration both systems receive events, and the security team's query tool reads both. See the "Event Gateway runbook" for the procedure of switching a source (link not valid) and the "Hub capacity sheet" for sizing (link not valid).

## 9. Open items

The final retention of the archive files depends on the decision of the compliance team. The catalog of actions will be moved from a spreadsheet into the repository. The naming of the sources (service name versus team name) is not unified; the collector accepts both for now.

## 10. Appendix: sizing

One hour of events at the peak rate is about ten gigabytes before compression and two to three gigabytes after. The archive grows by around sixty gigabytes a day. The stream keeps events for twenty-four hours so that the archive writer can catch up after a restart. A restart of the writer takes about three minutes and the catch-up time after it is below ten minutes in all tests so far.
