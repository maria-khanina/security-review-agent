Payment Gateway - meeting notes -> design (Mon)

Attendees: Jana, Pieter, Ruth

**Purpose** accept card payments from merchants, route to acquirers, publish payment events

**Architecture**
- Payments Edge Gateway (entrance)
- payments-core
- payments-db (PostgreSQL)
- Acquirer connector (third party)
- payment-events (Kafka)

**API**
- POST /v1/payments create
- GET /v1/payments/{paymentId}
- POST /v1/payments/{paymentId}/capture
- POST /v1/payments/{paymentId}/refunds
- GET /v1/payments list

**Flow** create -> authorize at the acquirer -> event `authorized` -> capture later -> event `captured`. Refund = new event.

**Decisions**
- payments-core stays one deployable for now (Pieter)
- We only upgrade the components that touch customer data; the rest stays on whatever version it has. (Ruth)
- Critical vulnerabilities are fixed in the next quarterly release. (Jana)
- Test accounts in production are removed within 7 days after the test ends.

**Actions**
- Jana: transaction records are kept for 7 years and deleted within 90 days after that
- Ruth: messages to customers contain no card numbers, passwords or images of identity documents
- Pieter: owner and deputy named in the service register, the register lists the personal data and each third party that receives data, e.g. the acquirer
- all: transactions above 10,000 EUR are held for review by the fraud team before settlement
- all: high alerts acknowledged within 15 minutes

Next meeting: Thursday.
