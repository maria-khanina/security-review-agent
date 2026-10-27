# notif svc - design

see wiki "notif v0" for old stuff (link dead, ask Pavel)

## what

- notifier reads events from domain-events (kafka), renders msg from template, sends to the email/sms provider, saves status
- 4 endpoints:
  - POST /v1/notifications - send (channel, recipient_id, template_id, locale) -> id, status, channel
  - GET /v1/notifications/{notificationId} - status
  - PUT /v1/templates/{templateId} - create/replace tamplate (subject, body)
  - GET /v1/notifications - list, filter by channel

## flow

1. event on domain-events
2. notifier picks template + channel
3. render, send to provider
4. provider reports delivery -> status updated (queued, sent, delivered, failed)

## retries

- provider timeout -> retry w/ backoff, 5 tries, then failed
- same notification id twice = no duplicate send

## security

- Internal callers prove their identity with a client certificate (mTLS) or a signed workload token, and anonymous internal calls are rejected.
- Internal users hold one of the service roles reader, operator or administrator, assigned by job: the support team needs reader, the platform team needs operator, and only two security leads need administrator.
- Production access is reviewed at least quarterly.
- Approved algorithms only; MD5, SHA-1, DES, 3DES and ECB are prohibited.
- No secrets in code, config, specs or infra definitions.
- Access to the central logs is limited to the on-call engineers of the owning team, who need it to investigate incidents, and to the security analysts, who need it to review audit events.
- DBs and brokers are in private subnets, not publicly reachable.
- Nothing travels unencrypted inside our network, because service-to-service and service-to-datastore links are encrypted.
- Key material is kept in KMS and separate from the data, and keys are rotated every year or sooner.
- Free-text fields from the delivery requests are stored verbatim, and they often contain more personal data than the message needs.
- The vendor receives the customer id and the email only, as these are the fields its notification task needs, and a data processing agreement covers the transfer.
- Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.
- Audit log entries are protected against silent modification and retained for a minimum of one year.
- Download links for reports with personal data work for 24 hours, and the files are encrypted in storage and deleted after 7 days.
- At startup the service fetches its secrets from the approved secret store.
- Access token lifetime is capped at 15 minutes, and using a refresh token rotates it.
- Queries are parameterized, no string concat of user input.
- CI must scan dependencies and images and critical vulnerabilities must be fixed within 14 days.

## logs

- The audit trail includes authentication failures, privilege changes and sensitive-data access.

