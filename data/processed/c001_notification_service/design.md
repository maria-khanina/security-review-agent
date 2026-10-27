# Notification Service

## Components

| Component | Type | Purpose |
|---|---|---|
| notifier | service | renders templates, sends messages |
| domain-events | Kafka topic | events that trigger messages |
| Email/SMS provider | third party | delivers email and SMS |

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | /v1/notifications | Send a notification |
| GET | /v1/notifications/{notificationId} | Delivery status |
| PUT | /v1/templates/{templateId} | Create or replace template |
| GET | /v1/notifications | List notifications |

## Flows

| From | To | Data |
|---|---|---|
| domain-events | notifier | event (type, customer id) |
| notifier | Email/SMS provider | recipient contact details, message body |

## Controls

| Area | Control |
|---|---|
| Rate limiting | The API enforces per-client rate limits. |
| Service auth | Calls between our own services carry a signed workload identity token or use mutual TLS, and the receiving service checks it. |
| Roles | Staff receive only the roles their job requires: support agents get the viewer role because they answer tickets, engineers get the operator role because they deploy and debug, and nobody gets the administrator role by default. |
| Access review | Production access reviewed quarterly. |
| Crypto | Approved algorithms only (no MD5, SHA-1, DES, 3DES, ECB). |
| Secrets | No secrets in code, config, specs or infra definitions. |
| Network | Databases and Kafka brokers are in private subnets, not publicly reachable. |
| Logging | Full request bodies are logged for debugging, including emails and card numbers. |
| Security events | Authentication failures, privilege changes and access to sensitive data are written to the logs. |
| Data minimization | A register of personal fields with the purpose of each is kept for the service, and anything that is not in the register is not stored. |
| Third parties | Before sending data to a partner we check the data processing agreement and strip every field that the partner does not need for its task, so only the agreed fields leave the platform. |
| Exports | Reports and exports with personal data are available only to authorized users, stored encrypted, and deleted after 7 days. |
| Queries | Reporting filters (status, channel, recipient) are built by joining the strings from the request, because the ORM could not express the optional combinations. |

Administrative and debug endpoints must not be reachable from the public internet.
On boot, the service pulls its credentials from the approved secret store.
Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks.
Access to the central logs is limited to the on-call engineers of the owning team, who need it to investigate incidents, and to the security analysts, who need it to review audit events.
Keys are managed in KMS, never stored next to the encrypted data, and rotated annually.
Access tokens must expire within 15 minutes and refresh tokens must be rotated on use.
Requests from outside are checked against the schema and rejected if they do not conform.

## Notes
Templates are versioned. Locale falls back to en.
| Retry | 3 attempts, exponential backoff
