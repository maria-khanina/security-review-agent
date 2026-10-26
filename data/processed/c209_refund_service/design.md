# Refund Service: Design Specification

## 1. Purpose and scope

This document specifies the Refund Service of Meridian Pay in accordance with company policy and the applicable regulatory framework. The service allows merchants and support agents to request, approve, track and cancel refunds of card payments. It replaces the refund module of the monolith and publishes the status of every refund as an event.

## 2. Architecture

The Refunds Gateway receives refund requests and approvals from merchant backends and support agents and passes them to refund-core. refund-core holds the lifecycle of a refund, stores the refund records with the references of the payments in refund-db (PostgreSQL) and publishes status events to refund-events (Kafka).

## 3. Interfaces

**POST /v1/refunds** requests a refund. The request carries payment_id, amount, currency, reason and requested_by; the response returns id, payment_id, status, amount and currency. A new refund has the status `requested`.

**GET /v1/refunds/{refundId}** returns one refund with id, payment_id, status, amount and currency.

**GET /v1/refunds** returns a page of refunds, newest first, with the same fields.

**POST /v1/refunds/{refundId}/approval** records a decision (`approve` or `reject`) with a comment and returns the refund. The decision is recorded for the agent who requested the refund, and refunds of any amount are executed by the person who requested them, without a further review.

**POST /v1/refunds/{refundId}/cancellation** cancels a refund that is still pending. The request carries a reason, and the response returns the refund.

## 4. Supporting documents

A support agent can attach a supporting document to a refund request, for example the scan of a receipt or the letter of a customer. refund-core receives the attached document together with the request and stores it with the refund record, so that the reviewer sees it on the refund. All uploaded files are scanned for malware before any other user or service can open them.

## 5. Merchant data

Refund records belong to the merchant of the original payment. Each query on merchant data is filtered by the tenant identifier taken from the authenticated token and never by a request parameter. Support agents see the refunds of the merchant for which they have opened the case.

## 6. Operation

Alerts about repeated failed logins, privilege changes and access to card data reach the on-call engineer within 15 minutes. refund-db is configured with point-in-time recovery and a retention of seven days.

The server recomputes the amount and the currency of each payment from the stored order and rejects a request whose values differ.

## 7. Status model and events

The statuses of a refund are `requested`, `approved`, `rejected`, `executed`, `cancelled` and `failed`. Every change of the status is published to refund-events with the refund id, the payment id, the old status, the new status and the time of the change. The consumers of the topic are the ledger, the notification service and the reporting jobs.

## 8. Failure handling

When the payment gateway does not confirm an executed refund within thirty seconds, refund-core keeps the status `approved` and retries the confirmation up to five times at growing intervals. After the fifth retry the status becomes `failed`, and the operations team receives the refund in the queue for manual handling.

## 9. Rollout

The service is introduced in two phases. In the first phase only support agents use it, for one month, while merchants continue to use the monolith. In the second phase merchants move in groups of fifty. The monolith module is switched off one month after the last group has moved.

## 10. Open questions

- Whether partial refunds need a separate status.
- The maximum number of supporting documents per refund request.
