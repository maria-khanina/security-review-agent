webhook dispatcher - sprint rusher doc, ship it friday

what: delivers callbacks to merchant endpoints, retries.
parts: dispatcher (svc), delivery-queue (queue), merchant endpoints (3rd party)
api: POST /v1/subscriptions, GET /v1/subscriptions/{id}, POST /v1/subscriptions/{id}/rotate-secret, GET /v1/deliveries, POST /v1/deliveries/{id}/retry
retries: 1m, 5m, 30m, 2h, 12h then failed

ops:
- Alerts about the dispatcher go to the platform team channel, they don't know the service but someone always reads it.

data and tests:
- Documents are deleted when the customer asks; no automatic deletion after the account is closed.
- No production data in test or development environments.
- Test accounts in production removed within 7 days after the test ends.

compliance:
- Messages to customers contain no card numbers, passwords or images of identity documents.
- Register lists the personal data and each third party that receives data from the dispatcher.
- Transactions above 10,000 EUR held for review by the fraud team before settlement.

next: dashboard for failed deliveries
