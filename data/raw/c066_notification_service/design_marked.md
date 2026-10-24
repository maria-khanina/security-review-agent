# Notification Service Design

## Part A (Priya, platform)

### 1. Purpose

The notifier sends email and SMS messages for the payment platform. It reads domain events from domain-events (Kafka), renders a message from a template, hands it to the Email and SMS provider and records the delivery status.

### 2. Components

- domain-events (Kafka): events that trigger messages.
- notifier: selects template and channel, renders, sends, tracks status.
- Email and SMS provider: external delivery service.

### 3. API

- POST /v1/notifications sends a notification (channel, recipient_id, template_id, locale) and returns id, status and channel.
- GET /v1/notifications/{notificationId} returns the delivery status.
- PUT /v1/templates/{templateId} creates or replaces a template (subject, body).
- GET /v1/notifications lists notifications, filterable by channel.

### 4. Security (platform controls)

- ⟦S:AUTH-02|Service-to-service calls are authenticated, either with mutual TLS between the workloads or with a signed workload identity token.⟧
- ⟦F2|A shared read-only login for the log platform is posted in the team wiki.⟧
- ⟦F3|Any authenticated caller can read any record if it knows the identifier.⟧
- ⟦S:AUTHZ-02|We keep roles small and per service, so an internal user only receives what their job requires.⟧
- ⟦S:API-01|All external inputs must be validated against a schema and rejected if invalid.⟧
- ⟦S:AUTHZ-04|Nothing administrative or meant for debugging can be called from outside our network.⟧
- ⟦S:AUTHZ-05|Access rights to production systems are reviewed at least quarterly.⟧
- ⟦S:CRYPTO-05|We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode.⟧
- ⟦S:NET-01|Databases and message brokers sit in private subnets and are not publicly reachable.⟧

### 5. Deployment

The notifier runs as two replicas that share a Kafka consumer group. Rolling updates replace one replica at a time.

---

## Part B (Tom, backend)

#### sending

so the worker (the notifier, I call it worker) picks the event, finds the template for the event type, fills in placeholders, sends via provider. if provider fails it retries 5 times with growing delay then marks failed. same notification id twice = not sent twice.

#### secrets (current state)

For now ⟦F1|the database password sits in the infrastructure code, and a sandbox API key is used as the default value in the specification, until the secret store is ready.⟧ Everything else the worker needs at runtime is already moved over:

#### logging

- ⟦S:LOG-01|Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.⟧

#### data

| area | rule |
|---|---|
| minimization | ⟦S:DATA-01|The service collects and stores only the personal data needed to deliver messages.⟧ |
| provider | ⟦S:DATA-03|Personal data is sent to the provider only under an approved data processing agreement, and only the fields required.⟧ |
| reports | ⟦S:DATA-05|Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.⟧

#### code and build

⟦S:API-05|User input reaches the database only as query parameters, never as part of the query text.⟧

#### templates

A template has a subject and a body with placeholders and one version per locale. The worker uses the newest version for the recipient's locale and falls back to English. A template with an unknown placeholder is rejected when it is saved.

##### Known mismatches

Part A says the notifier, Part B says worker; both are the same service. Part A says two replicas, the Part B runbook still says three (to be fixed). The old wiki page "Mailer v1" (link dead) used the name mailer-svc.
