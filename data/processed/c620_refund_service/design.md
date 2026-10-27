# Refund Service: Diagram Walkthrough

```
Merchant / Support agent
        |
 Refunds Gateway
        |
   refund-core ----> refund-events (Kafka)
        |
   refund-db (PostgreSQL)
```

## Reading the diagram

Merchants and support agents come in through the Refunds Gateway. It passes the calls to refund-core. The refund-core is a stateless service written in Java. It stores refunds in refund-db and publishes every change to refund-events.

## Operations

| Operation | Path |
|---|---|
| request a refund | POST /v1/refunds |
| retrieve | GET /v1/refunds/{refundId} |
| list | GET /v1/refunds |
| approve or reject | POST /v1/refunds/{refundId}/approval |
| cancel a pending refund | POST /v1/refunds/{refundId}/cancellation |

## State of a refund

```
requested -> approved -> paid
     |           |
  cancelled   rejected
```

## Commitments

- Records: transaction records are kept for 7 years and deleted within 90 days after that period. Documents uploaded by customers are deleted within 30 days after the account is closed.
- Components: no component is more than two major versions behind the latest release; the register shows each version.
- Tests: production data is not copied to test or development environments. Test accounts in production are removed within 7 days after the test ends.
- Messages: messages to customers contain no card numbers, passwords or images of identity documents.
- Callbacks: callbacks to customer endpoints are signed and carry a timestamp that the receiver can check against replay.
- Payments: Transactions of trusted merchants are never held for review, whatever the amount; all others above 10,000 EUR are held for review by the fraud team.
