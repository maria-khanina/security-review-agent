# notifier v2 - notes

old page: wiki/Notifier-Design (moved, search for it)

## what it does

- reads events from domain-events (kafka)
- picks template + channel, renders, sends via email/sms provider
- tracks status per notification
- endpoints: POST /v1/notifications, GET /v1/notifications/{notificationId}, PUT /v1/templates/{templateId}, GET /v1/notifications (filter by channel)

## fields

- send: channel, recipient_id, template_id, locale -> id, status, channel
- template: subject, body
- statuses: queued sent delivered failed

## retries

- provider error = retry w/ backoff, 5 tries, then failed
- dup notification id = ignored

## sec

- Internal service calls to notifier use mTLS or signed workload identity tokens.
- A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use.
- Connections to the database and between internal services use TLS.
- A caller can only read or change resources that belong to them or that they have been explicitly granted.
- We rotate service credentials at least every 90 days and straight away after any suspected exposure.
- Approved algs only; MD5, SHA-1, DES, 3DES and ECB are banned.
- Keys held in KMS, never next to the data, rotated at least annually.
- TLS certs are validated, verification never disabled.
- No secrets in code, config, specs or infra definitions.
- Only the support engineers of this service and the security analysts can read the central logs, because they use them to resolve customer tickets and to review security events; nobody else has access.
- Internal details such as stack traces, SQL and hostnames never appear in an error response.
- Runtime secrets are read from the secret store when the service starts.
- DB and brokers in private subnets, not publicly reachable.
- Egress to third parties limited to approved allowlist.

## data

- Before sending data to a partner we check the data processing agreement and strip every field that the partner does not need for its task, so only the agreed fields leave the platform.
- Staging is refreshed every night from a snapshot of production, with the real recipient data.

## logs / api / build

- Auth failures, privilege changes and sensitive data access are logged.
- All external inputs must be validated against a schema and rejected if invalid.
- Admin and debug endpoints are reachable only from the internal network, not from the public internet.
- The data inventory of the service lists every stored personal field with its purpose, and a field without a listed purpose is not collected.
- Inbound and outbound webhooks include an HMAC signature and a timestamp; verification of both is mandatory on the receiving side.
- Parameterized queries only.
- Staff receive only the roles their job requires: support agents get the viewer role because they answer tickets, engineers get the operator role because they deploy and debug, and nobody gets the administrator role by default.
- CI scans deps and images; critical vulns fixed within 14 days.
- Containers non-root, read-only rootfs where possible.
- Audit logs are written to tamper-evident storage with at least one year of retention.
