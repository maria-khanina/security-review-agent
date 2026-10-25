# Notification Service: Changes in Release 3

This document lists what changes in the Notification Service in release 3. Everything that is not mentioned here stays as described in the release 2 design (see "Notification Service - Design v2", section 4 and the appendix "Provider limits").

## Interfaces

The release adds the list call and changes the send call.

- **GET /v1/notifications** is new. It returns id, status and channel for the notifications in pages.
- **POST /v1/notifications** now takes a locale next to channel, recipient_id and template_id. The response still has id, status and channel.
- **GET /v1/notifications/{notificationId}** is unchanged and returns id, status and channel.
- **PUT /v1/templates/{templateId}** now returns the stored subject and body together with id.

## Data flow

The flow from domain-events (Kafka) to notifier and to the Email and SMS provider is unchanged. notifier now also sends the marketing messages of the campaign team, and the mails go out through the same channel as before. The provider still gets the contact details of the recipient and the message body.

## Customer rights

Requests of customers to see or delete their personal data are answered within 30 days and recorded in the request register. The register is the one of the Wallet Service, see the migration plan.

## Delivery

The pipeline of the platform team is unchanged, with one addition: credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour, where the old pipeline used a shared service account. Build artifacts are signed, and the signature is verified before deployment.

## Observability

The new locale field is added to the logs. Traces and metrics do not contain personal data or card data.

## Rollback

The pre-production environment of the Notification Service is not the same as production any more: it has no provider connection, another Kafka version and one tenth of the data, so rollback tests there are not trusted and the team does not rely on them. The old release stays deployed for two days after the switch (see the release 2 appendix).

## Rollout

The release goes to the internal staff first, then to all recipients after three days without a rise in the failed rate.

## Outdated

The section "Provider limits" of release 2 still names the provider of 2022 (stale; the contract changed).
