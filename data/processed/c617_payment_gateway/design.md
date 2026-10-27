# Payment Gateway: Roadmap and Design

We are very excited about where the gateway is going! This document describes the design as it will be after the next release.

## Vision

The gateway accepts card payments from merchants, routes them to acquirers and publishes payment events to the rest of the platform. In the next release we make it faster and simpler for merchants.

## Architecture

- **Payments Edge Gateway**: the single entrance for merchants
- **payments-core**: payments-core handles all the payment logic and talks to the acquirer connector and to the other services.
- **payments-db** (PostgreSQL): payments and their states
- **Acquirer connector**: third party
- **payment-events** (Kafka): events for other services

## API

POST /v1/payments, GET /v1/payments/{paymentId}, POST /v1/payments/{paymentId}/capture, POST /v1/payments/{paymentId}/refunds, GET /v1/payments.

## Quality commitments (the exciting part!)

- Transaction records are kept for 7 years and deleted within 90 days after that.
- Critical vulnerabilities are fixed in production within 7 days after they are published.
- Production data is not copied to test or development environments.
- Test accounts in production are removed within 7 days after the test ends.
- Messages to customers do not contain card numbers, passwords or images of identity documents.
- The service register names an owner and a deputy.
- On-call alerts are acknowledged automatically by the paging tool after 5 minutes, so the response time is always excellent.
- Callbacks to merchants are signed with the shared secret, they carry no timestamp.

## Next release

Faster capture, one-click refunds, a merchant status page.
