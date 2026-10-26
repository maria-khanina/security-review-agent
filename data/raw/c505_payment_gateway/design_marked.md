# payment gateway notes

ok so this is the new payment gateway design, I write it as I think so the order is not perfect. merchants send payment requests with a card token to the Payments Edge Gateway, the edge passes them to payments-core, payments-core talks to the acquirer connector and writes the payment into payments-db and publishes the status on payment-events (Kafka). endpoints are the same five as before: create a payment (amount, currency, card_token, merchant_id, reference -> id, status, amount, currency, last4, merchant_id), get a payment, capture with an amount, refund with amount and reason, and list payments.

about where the data lives, ⟦S:RES-01|personal data of customers in the EU is stored and processed only in regions of the EU.⟧ that was a decision of the architecture board (TBD link) and the database was created in the Frankfurt region.

then the part about money features. ⟦F1|We have a kill switch for refunds and captures, but it is a configuration flag, so after somebody flips it the service needs a restart to read it, and a restart of payments-core takes a few minutes.⟧ I know it is not great (TBD ticket to read the flag at runtime).

what else. payments-core runs as three replicas. ⟦F2|payments-core writes traces and metrics for every payment, and the dashboards show latency and error rate per endpoint and per acquirer.⟧ the acquirer timeout is three seconds, payments stay pending and we ask five times and then decline with acquirer_timeout (TBD should the number of retries be configurable per acquirer).

⟦S:OBS-02|Health check results and error rates are published to the shared dashboard every minute, and an alert fires when the error rate stays above 2% for five minutes.⟧

for the build, ⟦S:PIP-01|credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour⟧ and ⟦S:PIP-02|build artifacts are signed and the signature is verified before deployment.⟧ for traffic, ⟦S:CAP-01|public endpoints answer HTTP 503 instead of queueing when their capacity is exhausted.⟧

⟦S:PRV-03|Each use of customer data is tied to a purpose in the privacy notice shown at sign-up, and a new purpose needs a new notice and new consent.⟧
⟦S:CHG-01|A second engineer reviews each production change before it is deployed.⟧

rollout is three waves, new merchants first, then groups of about fifty existing merchants, then we switch off the old endpoints a month after the last group (TBD date). open questions: filter by status on the list call, a separate event for partial captures, which acquirer moves first.
