# Payment Gateway: Service Design

Owner: Payments Platform team
Status: approved for build
Last updated: this quarter

## 1. Background and goals

The Payment Gateway accepts card payments from our merchants, routes them to the acquiring banks and publishes the status of every payment as an event for the other platform services. Today the same functions are spread over the old monolith, and each merchant integration depends on details of that monolith. This document describes the new service that replaces those functions without changing the contract that merchants see.

The goals for the first release are:

- keep the public contract of the five payment endpoints unchanged for the merchants;
- reduce the time between a merchant request and the answer of the acquirer to under two seconds at the median;
- publish a status event for every change of a payment, so that the ledger, the notification service and the reporting jobs no longer poll a table.

## 2. Non-goals

- Settlement and payouts to merchants stay in the settlement module for now.
- Card network disputes are handled by the operations team in their own tooling.
- Currency conversion is not part of this release; the currency of a payment is the currency of the merchant account.

## 3. Components

The service consists of four parts. The Payments Edge Gateway is the single entrance for merchant traffic and passes validated requests to payments-core. payments-core holds the payment state machine and talks to the acquirer through the Acquirer connector. payments-db (PostgreSQL) stores the payment records, and the payment-events topic (Kafka) carries the status events.

⟦F3|payments-core runs as three replicas behind the internal load balancer and is deployed by the platform team in rolling steps, one replica at a time.⟧ The Acquirer connector is a thin adapter that maps our payment model to the message format of each acquirer, and it keeps no state of its own.

## 4. Behavior of each endpoint

**POST /v1/payments** creates a payment. The request carries amount, currency, card_token, merchant_id and reference. The response returns id, status, amount, currency, last4 and merchant_id. ⟦F1|The create call looks at the idempotency key of the request and returns the stored answer when the key was seen before; capture and refund calls rely on the status of the payment to avoid a second execution.⟧ A payment is created in the status `authorized` when the acquirer approves the amount, and in `declined` otherwise.

**GET /v1/payments/{paymentId}** returns one payment with the fields id, status, amount, currency, last4 and merchant_id.

**POST /v1/payments/{paymentId}/capture** captures an authorized payment. The request carries the amount, which may be lower than the authorized amount for partial captures. The response returns the same fields as the create call. A payment that has been captured cannot be captured again.

**POST /v1/payments/{paymentId}/refunds** refunds a captured payment, fully or partly. The request carries amount and reason, and the response returns id, status and amount. ⟦S:PAY-02|Refunds and reversals above 1,000 EUR need the approval of a second person, and the person who asked for the refund cannot approve it themselves.⟧ The sum of all refunds of a payment may not exceed the captured amount.

**GET /v1/payments** lists payments of a merchant with paging, newest first. Support staff use a separate internal search for questions from merchants. ⟦F2|The search reads the payments of all merchants from payments-db and filters the rows in the application by the merchant that the support agent typed in.⟧

## 5. Data model

A payment has an id, the merchant id, the amount and the currency, the status, the last four digits of the card, the reference of the merchant, the id of the acquirer message and the timestamps of each status change. Refunds are separate records that point to the payment. Amounts are stored in the smallest unit of the currency as whole numbers.

The statuses are `authorized`, `declined`, `captured`, `refunded`, `partially_refunded` and `expired`. An authorization that is not captured within seven days moves to `expired`.

## 6. Failure modes and retries

When the acquirer does not answer within three seconds, payments-core keeps the payment in `pending` and asks the acquirer for the result up to five times, with growing pauses between the attempts. If there is still no answer, the payment is marked `declined` with the reason `acquirer_timeout`, and the merchant receives the final status in the event stream and in the next read of the payment.

When Kafka is not reachable, payments-core writes the event into an outbox table in payments-db and a relay job publishes it later, in order. Events can therefore arrive late, but they are never lost and never reordered for one payment.

## 7. Third-party components and recovery

⟦S:TPC-01|Every third-party SDK or library, including the acquirer SDKs, is approved before its first use, and the list of approved components is reviewed every six months.⟧ ⟦S:DR-01|payments-db has point-in-time recovery switched on, with seven days of retention.⟧

## 8. Rollout plan

The rollout has three steps. First, new merchants are onboarded on the new service while existing merchants stay on the monolith. Second, existing merchants move in groups of about fifty, starting with the ones that send the lowest volume. Third, the old endpoints in the monolith are switched off after a month without traffic.

Each group is observed for one week before the next group starts. If the share of declined payments of a group rises by more than two points compared with the week before the move, the group moves back.

## 9. Open questions

- Should the list endpoint support filtering by status in the first release?
- Do we publish a separate event for partial captures, or is the status change enough?
- Which acquirer is the first one to move to the new connector?
