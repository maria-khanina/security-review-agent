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
- Access tokens expire within 15 min; refresh tokens rotated on use.
- Traffic between services, and to data stores and brokers, is encrypted in transit.
- Approved algs only; MD5, SHA-1, DES, 3DES and ECB are banned.
- Keys held in KMS, never next to the data, rotated at least annually.
- TLS certs are validated, verification never disabled.
- No secrets in code, config, specs or infra definitions.
- Runtime secrets come from the approved secret store at startup.
- DB and brokers in private subnets, not publicly reachable.
- Egress to third parties limited to approved allowlist.

## data

- Personal data to third parties only under an approved DPA, only required fields.
- No real personal or card data in non-prod.

## logs / api / build

- Auth failures, privilege changes and sensitive data access are logged.
- Webhook payloads signed, signatures verified (in and out).
- Parameterized queries only.
- CI scans deps and images; critical vulns fixed within 14 days.
- Containers non-root, read-only rootfs where possible.
