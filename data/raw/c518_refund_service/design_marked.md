# Refund Service - Architecture Description

## 1. Purpose

The Refund Service lets merchants and support agents request, approve and track refunds of card payments. It separates the decision about a refund from the movement of money, keeps a complete record of every refund and informs other services of the outcome. This document describes the architecture on the level that is needed to build and review the service.

## 2. Context

Merchant backends and support agents are the users of the service. They reach it through the public Refunds Gateway. Behind the gateway the service refund-core holds the lifecycle of a refund, refund-db (PostgreSQL) holds the refund records with references to the payments, and the Kafka topic refund-events carries the status events to the other services of the platform.

## 3. Quality goals

The service must be correct before it is fast: a refund is never booked twice, and every refund can be explained afterwards. Availability matters less than correctness, because a refund can wait for several minutes without harm.

## 4. Building blocks

### 4.1 Refunds Gateway

⟦F3|The Refunds Gateway is the single entry point of the service. It authenticates the callers and passes the requests to refund-core.⟧

### 4.2 refund-core

refund-core owns the state machine of a refund: requested, approved or rejected, paid, or cancelled. Each transition is stored together with the actor who caused it.

### 4.3 refund-db

refund-db keeps one row per refund with payment_id, amount, currency, reason and the actor. Rows are never deleted.

### 4.4 refund-events

Each transition produces an event with the id of the refund and the new status. Consumers read the events at their own pace.

## 5. Interfaces

- **POST /v1/refunds** takes payment_id, amount, currency, reason and requested_by and returns id, payment_id, status, amount and currency.
- **GET /v1/refunds/{refundId}** and **GET /v1/refunds** return the same five fields.
- **POST /v1/refunds/{refundId}/approval** takes decision and comment and returns the same fields.
- **POST /v1/refunds/{refundId}/cancellation** takes reason and returns the same fields.

## 6. Cross-cutting concepts

### 6.1 Operations in an emergency

The service has a kill switch for refunds, because a fault in the approval logic could pay money out wrongly. ⟦F1|Only one engineer knows where the kill switch is and how to use it.⟧

### 6.2 Delivery

⟦S:PIP-01|Credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour.⟧

### 6.3 Database changes

⟦F2|Database migrations of the service cannot be rolled back, and nothing is planned for that case.⟧
⟦S:PRV-03|Each use of customer data is tied to a purpose in the privacy notice shown at sign-up, and a new purpose needs a new notice and new consent.⟧

### 6.4 Observability

⟦S:OBS-01|Traces and metrics do not contain personal data or card data.⟧ The dashboards show the number of refunds per status and the age of the oldest pending refund.

⟦S:CHG-01|Every change to production is reviewed by a second engineer before deployment.⟧

## 7. Decisions

1. Refunds are idempotent by the pair of payment_id and a client-supplied reference.
2. Approval needs a second person for amounts above the limit of the merchant.
3. Events are published after the database transaction has committed, by an outbox process.

## 8. Risks

A wrong approval rule is the main risk of the service, which is why every transition is stored with its actor. The second risk is the dependency on the acquirer for the payout.
