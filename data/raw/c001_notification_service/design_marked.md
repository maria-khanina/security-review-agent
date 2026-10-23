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
| Rate limiting | ⟦F1|The API enforces per-client rate limits.⟧ |
| Service auth | ⟦S:AUTH-02|Calls between our own services carry a signed workload identity token or use mutual TLS, and the receiving service checks it.⟧ |
| Roles | ⟦S:AUTHZ-02|Internal users get only the roles their job needs, defined per service.⟧ |
| Access review | ⟦S:AUTHZ-05|Production access reviewed quarterly.⟧ |
| Crypto | ⟦S:CRYPTO-05|Approved algorithms only (no MD5, SHA-1, DES, 3DES, ECB).⟧ |
| Secrets | ⟦S:SECRET-01|No secrets in code, config, specs or infra definitions.⟧ |
| Network | ⟦S:NET-01|Databases and Kafka brokers are in private subnets, not publicly reachable.⟧ |
| Logging | ⟦F2|Full request bodies are logged for debugging, including emails and card numbers.⟧ |
| Security events | ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are written to the logs.⟧ |
| Data minimization | ⟦S:DATA-01|Only the contact details needed for the channel are stored.⟧ |
| Third parties | ⟦S:DATA-03|The provider receives only the recipient contact and the message body, under an approved DPA.⟧ |
| Exports | ⟦S:DATA-05|Delivery reports containing personal data need authorization, are encrypted in storage and expire.⟧ |
| Queries | ⟦S:API-05|Parameterized queries only.⟧ |

## Notes
Templates are versioned. Locale falls back to en.
| Retry | 3 attempts, exponential backoff
