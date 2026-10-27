# Refund Service - Roadmap Design

Where we are going: refunds in seconds, not days!

## Architecture

- **Refunds Gateway**: the entrance for merchants and agents
- **refund-core**: the service
- **refund-db** (PostgreSQL): refunds and their states
- **refund-events** (Kafka): every change is published

## Interface

`POST /v1/refunds`, `GET /v1/refunds/{refundId}`, `GET /v1/refunds`, `POST /v1/refunds/{refundId}/approval`, `POST /v1/refunds/{refundId}/cancellation`.

## Quality commitments

- Every operation that moves money takes an idempotency key, and a repeated request with the same key does not move the money again.
- The daily outgoing transfers of a customer are limited by the limit table, and a change of a limit needs the approval of a second employee.
- A replaced API version is kept for 12 months, and its removal is announced 90 days in advance.
- Breaking changes of the API are released only as a new version of the API.
- The merchant sandbox contains only generated data and runs separately from production.
- The dead-letter queue of refund-events is examined once a week.
- Messages are deleted from the queue after they are processed.
- Support agents see card numbers and document numbers only in masked form.
- A change of the phone number or the email address needs a one-time code that is sent to the old contact data.
