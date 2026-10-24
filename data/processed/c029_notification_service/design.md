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
- Approved algs only; MD5, SHA-1, DES, 3DES and ECB are banned.
- Keys held in KMS, never next to the data, rotated at least annually.
- TLS certs are validated, verification never disabled.
- No secrets in code, config, specs or infra definitions.
- Only authorized staff can access the central logs.
- Internal details such as stack traces, SQL and hostnames never appear in an error response.
- Runtime secrets are read from the secret store when the service starts.
- DB and brokers in private subnets, not publicly reachable.
- Egress to third parties limited to approved allowlist.

## data

- Personal data to third parties only under an approved DPA, only required fields.
- Staging is refreshed every night from a snapshot of production, with the real recipient data.

## logs / api / build

- Auth failures, privilege changes and sensitive data access are logged.
- All external inputs must be validated against a schema and rejected if invalid.
- Admin and debug endpoints are reachable only from the internal network, not from the public internet.
- Inbound and outbound webhooks include an HMAC signature and a timestamp; verification of both is mandatory on the receiving side.
- Parameterized queries only.
- CI scans deps and images; critical vulns fixed within 14 days.
- Containers non-root, read-only rootfs where possible.
