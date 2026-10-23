# Audit Log Pipeline v2 - what changes compared to v1

Based on: Audit pipeline v1 (the "audit-hub", 2023). Everything not listed here stays as it was in v1.

## What stays the same

- The pipeline collects audit events from the platform services and keeps them for the security team.
- Events have the same six fields as in v1: source, actor, action, object, result, time.
- The security team reads the archive through the same query tool as before.
- Sources send events by the internal API; the format of the request does not change.

## What is new

**audit-collector replaces audit-hub.** The old hub wrote straight to the search cluster. The new audit-collector validates the event, stamps it and puts it on audit-stream (MSK). audit-collector reads events from the platform services and writes them to audit-stream, and the collector and the stream run in the pipeline account.

**The archive moves to S3.** audit-stream feeds a writer that stores hourly batches in the audit archive (S3). The search cluster is switched off after the migration.

**Infrastructure as code.** Everything is in Terraform now: `audit_key`, `audit_stream`, `audit_archive`, `pipeline_audit`, `audit_backups` and `pipeline_policy`. In v1 the cluster was created by hand.

## Controls

The security properties of the pipeline are the ones the old hub had, restated here because the old document is out of date (it still talks about the search cluster and the VPN gateway of 2022).

- Calls between our own services carry a signed workload identity token or use mutual TLS, and the receiving service checks it.
- Access tokens expire within 15 minutes; refresh tokens are rotated on use.
- The databases and object stores that hold PII use AES-256 encryption at rest.
- We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.
- Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.
- Clients check the certificate chain and host name on every TLS connection and have no insecure mode.
- Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
- At startup the service fetches its secrets from the approved secret store.
- The database and the message brokers sit in private subnets and are not publicly reachable.
- The audit archive blocks public access and is private by default.
- Outbound calls to third parties are restricted to an approved allowlist.
- Authentication failures, privilege changes and access to sensitive data are written to the logs.
- Personal data goes to third parties only under an approved data processing agreement, and only the required fields are sent.
- Real customer and card data is kept out of dev, test and staging.
- Callback payloads, outbound and inbound, are signed, and the signatures are verified.
- All queries use bound parameters instead of string concatenation.
- CI scans dependencies and images, and critical vulnerabilities are fixed within 14 days.
- Containers run as a non-root user, with a read-only root filesystem where possible.

## Known deviations carried over from v1

- Tokens and API keys appear in the debug logs of the gateway. This was true in v1 and the gateway is not part of this change, so it is not fixed here.
- Backup copies of the archive are not encrypted, and restores are tried only after an incident. The backup vault is new in v2 and was set up like the v1 backups.

## Migration

The events of the last twelve months are copied from the search cluster to the archive in the first month. The collector is switched on for three pilot services in week two and for the rest in week six. Reference: v1 runbook, page "Audit hub operations" (page was moved, link not valid).
