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

- ⟦S:IDM-01|Every operation that moves money takes an idempotency key, and a repeated request with the same key does not move the money again.⟧
- ⟦S:LIM-01|The daily outgoing transfers of a customer are limited by the limit table, and a change of a limit needs the approval of a second employee.⟧
- ⟦S:VER-01|A replaced API version is kept for 12 months, and its removal is announced 90 days in advance.⟧
- ⟦S:VER-02|Breaking changes of the API are released only as a new version of the API.⟧
- ⟦S:SBX-01|The merchant sandbox contains only generated data and runs separately from production.⟧
- ⟦F1|The dead-letter queue of refund-events is examined once a week.⟧
- ⟦S:MSG-02|Messages are deleted from the queue after they are processed.⟧
- ⟦S:SUP-01|Support agents see card numbers and document numbers only in masked form.⟧
- ⟦S:SUP-02|A change of the phone number or the email address needs a one-time code that is sent to the old contact data.⟧
