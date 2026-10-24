# Notification svc

## What
- sends email / sms / push when a domain event arrives
- one place for templates (was spread over the monolith)
- provider can be swapped without touching callers

## Parts
- notifier (the service)
- domain-events topic (Kafka) in
- Email and SMS provider out (their SDK in the notifier)

## API
- POST /v1/notifications: channel, recipient_id, template_id, locale -> id, status, channel
- GET /v1/notifications/{id}: -> id, status, channel
- PUT /v1/templates/{id}: subject, body -> id, subject, body
- GET /v1/notifications: list

## Behaviour
- one message per event
- provider temp failure: retry 1 min, 5 min, 15 min, then failed
- same recipient + same event type within 1 min: merged
- no template for locale: English, fallback recorded
- statuses: queued, sent, delivered, failed

## Libs
- Every third-party SDK or library needs approval before its first use, and the list of approved components is reviewed every six months.
- provider SDK is on the list (TBD version pin)

## Incidents
- The incident procedure for the notifier is the one that was written for the old monolith, nobody has updated it for the new service.

## Rollout
- txn messages first, then account messages, reminders last
- old code keeps sending 2 weeks per step, compare job reports diffs
- then old code removed

## TBD
- keep delivery receipts > 30 days?
- push provider in release 2?
