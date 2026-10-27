notifier - sprint rusher doc

what: consumes domain events, builds email/SMS/push, sends via provider
parts: notifier (service), domain-events (Kafka), Email and SMS provider (3rd party)
api: POST /v1/notifications, GET /v1/notifications/{id}, PUT /v1/templates/{id}, GET /v1/notifications

must haves
- sandbox: generated data only, separate from production
- unprocessable messages go to the dead-letter queue, examined within one working day
- processed messages are deleted from the queue
- agents see card numbers and document numbers only masked
- phone/email change needs a one-time code sent to the old contact data

next: digest mails
