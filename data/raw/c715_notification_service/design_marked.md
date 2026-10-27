# Notification Service (copy-paste from three older docs)

## Part A: What it does

The notifier takes domain events from Kafka (domain-events), builds an email, a text message or a push message from a template and hands it to the Email and SMS provider. Delivery status comes back by callback.

## Part B: Endpoints

POST /v1/notifications, GET /v1/notifications/{notificationId}, PUT /v1/templates/{templateId}, GET /v1/notifications.

## Part C: Staging (from the wiki)

⟦F1|The sandbox is a copy of the production database in which only the names are changed.⟧

## Part D: Queue (from the ops page)

⟦F2|Failed messages are retried forever, so one bad message can block a queue.⟧ ⟦S:MSG-02|Messages are deleted from the queue after they are processed.⟧

## Part E: Jobs (from the old runbook)

⟦F3|The service account of the digest job has a password that engineers use to log in when they debug.⟧

## Part F: Commitments

- ⟦S:VER-02|Breaking changes of the API are released only as a new version of the API.⟧
- ⟦S:SUP-01|Support agents see card numbers and document numbers only in masked form.⟧
