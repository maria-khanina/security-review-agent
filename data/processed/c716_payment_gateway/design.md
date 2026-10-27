# Payment Gateway - Introduction for New Developers

## Step 1: What is it?

The payment gateway accepts card payments from merchants, routes them to the acquirers and publishes payment events. Merchants call the Payments Edge Gateway, which forwards to payments-core. payments-core stores payments in payments-db (PostgreSQL), calls the Acquirer connector (third party) and publishes events to payment-events (Kafka).

## Step 2: The API

`POST /v1/payments`, `GET /v1/payments/{paymentId}`, `POST /v1/payments/{paymentId}/capture`, `POST /v1/payments/{paymentId}/refunds`, `GET /v1/payments`.

## Step 3: House rules

Please learn these.

- Balances are reconciled with the ledger every day, and a difference of more than 0.01 EUR is reported to the finance team within 24 hours.
- Differences found in a reconciliation are resolved within 5 working days.
- Every operation that moves money takes an idempotency key, and a repeated request with the same key does not move the money again.
- The daily outgoing transfers of a customer are limited by the limit table, and a change of a limit needs the approval of a second employee.
- A replaced API version is kept for 12 months, and its removal is announced 90 days in advance.
- Fields of the API are renamed in place when it makes the API cleaner, and customers are told in the chat.
- Every scheduled job runs with its own service account, which cannot log in interactively.
- A change of the phone number or the email address needs a one-time code that is sent to the old contact data.

## Step 4: Support tools

In the support tools, card numbers are masked on the search page, the detail page shows the full number.
