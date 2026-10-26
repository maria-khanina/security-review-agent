# Notification Service - Flow View

```
 domain-events (Kafka) ──events──▶ notifier ──contact + body──▶ Email and SMS provider
                                      ▲
                          internal callers (REST)
```

## Boxes

- **domain-events (Kafka)**: events that trigger messages.
- **notifier**: renders the template, sends the message, keeps the delivery status.
- **Email and SMS provider**: external delivery of the message.

Internal exposure only. The REST calls of notifier are used by other services of the platform inside the private network.

## Arrows and calls

- domain-events ▶ notifier: event with recipient_id and template id.
- POST /v1/notifications: channel, recipient_id, template_id, locale ▶ id, status, channel.
- GET /v1/notifications/{notificationId}: ▶ id, status, channel.
- PUT /v1/templates/{templateId}: subject, body ▶ id, subject, body.
- GET /v1/notifications: ▶ id, status, channel.
- notifier ▶ provider: contact details of the recipient and the text of the message.

## Captions

**Customer rights.** ⟦S:PRV-01|Requests of customers to see or delete their personal data are answered within 30 days and recorded in the request register.⟧

**Consent.** ⟦F1|The consent text for marketing messages is overwritten when it is changed, and the earlier versions are not kept.⟧

**Tracing.** ⟦F2|Traces record the full request, including the name and the email of the customer, for every call of notifier.⟧

**Delivery.**

```
 commit ▶ build ▶ sign ▶ verify ▶ deploy
```

⟦S:PIP-01|Credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour.⟧ ⟦S:PIP-02|Build artifacts are signed, and the signature is verified before deployment.⟧ ⟦S:CHG-02|Every change to production has a rollback plan that has been tested in a pre-production environment.⟧

⟦S:CHG-01|No change reaches production without the review of an engineer other than the author.⟧

⟦S:PRV-03|The service processes personal data only for the purposes listed in the privacy notice, and a new purpose is published to customers before the data is used.⟧

**Failure.** Provider timeout 10 s ▶ retry 3 times ▶ status `failed`. Kafka down ▶ outbox (TBD size).

**Open.** Template versioning (TBD). See also the diagram in the Wallet Service design.
