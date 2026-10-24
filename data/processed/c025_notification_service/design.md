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
- Internal users get only the roles their job needs; roles are defined per service.
- Production access is reviewed at least quarterly.
- Approved algorithms only; MD5, SHA-1, DES, 3DES and ECB are prohibited.
- No secrets in code, config, specs or infra definitions.
- Access to centralized logs must be limited to authorized staff.
- DBs and brokers are in private subnets, not publicly reachable.
- Free-text fields from the delivery requests are stored verbatim, and they often contain more personal data than the message needs.
- Personal data goes to third parties only under an approved DPA, and only the fields required.
- Download links for reports with personal data work for 24 hours, and the files are encrypted in storage and deleted after 7 days.
- At startup the service fetches its secrets from the approved secret store.
- Queries are parameterized, no string concat of user input.

## logs

- The audit trail includes authentication failures, privilege changes and sensitive-data access.

