# Audit Log Pipeline v2 - what changes compared to v1

Based on: Audit pipeline v1 (the "audit-hub", 2023). Everything not listed here stays as it was in v1.

## What stays the same

- The pipeline collects audit events from the platform services and keeps them for the security team.
- Events have the same six fields as in v1: source, actor, action, object, result, time.
- The security team reads the archive through the same query tool as before.
- Sources send events by the internal API; the format of the request does not change.

## What is new

**audit-collector replaces audit-hub.** The old hub wrote straight to the search cluster. The new audit-collector validates the event, stamps it and puts it on audit-stream (MSK). ⟦F2|audit-collector reads events from the platform services and writes them to audit-stream, and the collector and the stream run in the pipeline account.⟧

**The archive moves to S3.** audit-stream feeds a writer that stores hourly batches in the audit archive (S3). The search cluster is switched off after the migration.

**Infrastructure as code.** Everything is in Terraform now: `audit_key`, `audit_stream`, `audit_archive`, `pipeline_audit`, `audit_backups` and `pipeline_policy`. In v1 the cluster was created by hand.

## Controls

The security properties of the pipeline are the ones the old hub had, restated here because the old document is out of date (it still talks about the search cluster and the VPN gateway of 2022).

- ⟦S:AUTH-02|Internal service calls are authenticated with mutual TLS or signed workload identity tokens.⟧
- ⟦S:AUTH-03|Access tokens expire within 15 minutes; refresh tokens are rotated on use.⟧
- ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧
- ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
- ⟦S:CRYPTO-06|Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.⟧
- ⟦S:CRYPTO-07|Services validate TLS certificates and never disable verification.⟧
- ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧
- ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧
- ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧
- ⟦S:NET-02|The audit archive blocks public access and is private by default.⟧
- ⟦S:NET-04|Services that call third parties have their egress restricted to an approved allowlist.⟧
- ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧
- ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧
- ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧
- ⟦S:API-03|Callback payloads, outbound and inbound, are signed, and the signatures are verified.⟧
- ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧
- ⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧
- ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧

## Known deviations carried over from v1

- ⟦F1|Tokens and API keys appear in the debug logs of the gateway.⟧ This was true in v1 and the gateway is not part of this change, so it is not fixed here.
- ⟦F3|Backup copies of the archive are not encrypted, and restores are tried only after an incident.⟧ The backup vault is new in v2 and was set up like the v1 backups.

## Migration

The events of the last twelve months are copied from the search cluster to the archive in the first month. The collector is switched on for three pilot services in week two and for the rest in week six. Reference: v1 runbook, page "Audit hub operations" (page was moved, link not valid).
