webhook dispatcher - stream of thoughts

so the dispatcher takes events from the delivery-queue and posts them to the merchant callback endpoints which are third party, retries after 1 minute 5 minutes 30 minutes 2 hours 12 hours then failed and the merchant can retry by hand with POST /v1/deliveries/{deliveryId}/retry, subscriptions are POST /v1/subscriptions and GET /v1/subscriptions/{subscriptionId} and the secret can be rotated with POST /v1/subscriptions/{subscriptionId}/rotate-secret and the list of attempts is GET /v1/deliveries

money wise: only the payment events are sent with an idempotency key; for transfers the receiver has to make sure that it does not process twice.

and then compliance wants these: balances are reconciled with the ledger every day and a difference of more than 0.01 EUR is reported to the finance team within 24 hours, , a replaced API version is kept for 12 months and its removal is announced 90 days in advance, breaking changes of the API are released only as a new version of the API, , messages that cannot be processed go to a dead-letter queue, which is examined within one working day, messages are deleted from the queue after they are processed,

TBD what the failed delivery mail says
