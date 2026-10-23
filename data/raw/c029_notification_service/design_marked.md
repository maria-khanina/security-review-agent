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

- ⟦S:AUTH-02|Internal service calls to notifier use mTLS or signed workload identity tokens.⟧
- ⟦S:AUTH-03|A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use.⟧
- ⟦S:CRYPTO-04|Connections to the database and between internal services use TLS.⟧
- ⟦S:CRYPTO-05|Approved algs only; MD5, SHA-1, DES, 3DES and ECB are banned.⟧
- ⟦S:CRYPTO-06|Keys held in KMS, never next to the data, rotated at least annually.⟧
- ⟦S:CRYPTO-07|TLS certs are validated, verification never disabled.⟧
- ⟦S:SECRET-01|No secrets in code, config, specs or infra definitions.⟧
- ⟦S:SECRET-02|Runtime secrets are read from the secret store when the service starts.⟧
- ⟦S:NET-01|DB and brokers in private subnets, not publicly reachable.⟧
- ⟦S:NET-04|Egress to third parties limited to approved allowlist.⟧

## data

- ⟦S:DATA-03|Personal data to third parties only under an approved DPA, only required fields.⟧
- ⟦S:DATA-04|No real personal or card data in non-prod.⟧

## logs / api / build

- ⟦S:LOG-01|Auth failures, privilege changes and sensitive data access are logged.⟧
- ⟦S:API-03|Webhook payloads signed, signatures verified (in and out).⟧
- ⟦S:API-05|Parameterized queries only.⟧
- ⟦S:OPS-01|CI scans deps and images; critical vulns fixed within 14 days.⟧
- ⟦S:OPS-02|Containers non-root, read-only rootfs where possible.⟧
