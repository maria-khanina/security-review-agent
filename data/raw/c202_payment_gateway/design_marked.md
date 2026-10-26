# Payment Gateway: Next-Generation Payments Platform

## Executive summary

The Payment Gateway is the centerpiece of our merchant acquiring strategy. It gives merchants a frictionless, enterprise-grade way to accept card payments and gives the business a flexible foundation for the next three years of growth in the EU and UK. By moving payment processing out of the monolith, we unlock faster onboarding of merchants, faster releases and a better experience for every partner.

## Business value

- Merchants go live in days instead of weeks, which supports the growth targets of the Merchant Experience pillar.
- Acquirers can be added or switched without touching the merchant integration, so we can negotiate better rates.
- Status events for every payment feed finance, notifications and reporting in near real time, which removes manual reconciliation.

## Product scope

The service offers five capabilities: create a payment, read a payment, capture, refund and list payments. Each capability maps one to one to an endpoint of the existing merchant contract, so merchants do not need to change their code. Settlement and payouts remain in the settlement module (see Appendix C for the planned migration).

## How a payment flows

A merchant backend calls the Payments Edge Gateway with the payment request. The Payments Edge Gateway forwards the request to payments-core, the engine that holds the lifecycle of a payment. payments-core calls the Acquirer connector, which translates the request for the acquirer of the merchant, and stores the result in payments-db. Every status change is published to the payment-events topic.

⟦F2|The Payments Edge Gateway is the single front door for all merchant calls and keeps the experience simple and fast for the merchant.⟧

### Creating a payment

The merchant sends the amount, the currency, a card token, the merchant id and its own reference. ⟦F1|To keep checkout as fast as possible, payments-core takes the amount and the currency of the payment from the request that arrives from the merchant and does not compare them with the order again.⟧ The answer contains the id, the status, the amount, the currency, the last four digits of the card and the merchant id.

### Capture and refund

Capture takes an amount that can be lower than the authorized amount. A refund takes an amount and a reason. ⟦S:PAY-02|Any refund or reversal above 1,000 EUR is approved by a second person, and the requester of the operation can never approve it.⟧ We expect about one refund for every forty captured payments in the first year.

⟦S:IR-02|The service has a written incident runbook, a named on-call owner who can be paged at any hour, and the runbook is rehearsed at least twice a year.⟧

### Reading and listing

A payment can be read by its id, and the list endpoint returns the payments of a merchant, newest first, in pages.

## Data and storage

payments-db holds payments, refunds and the history of status changes. ⟦S:TEN-02|Merchant data in payments-db is separated through row-level security, so each merchant sees only its own rows.⟧ ⟦S:DR-01|Point-in-time recovery is switched on for payments-db, with seven days of retention.⟧

⟦S:DR-02|Recovery of the service is required within 4 hours, which is demonstrated by an annual failover exercise.⟧

## Partners and components

Our acquirers and their SDKs are strategic partners. ⟦S:TPC-01|Every third-party SDK or library is approved before first use, and the list of approved components is reviewed every six months.⟧

## Rollout approach

We will roll out in three waves: new merchants, then the existing merchants in groups, then the final switch-off of the old endpoints. Each wave is measured with the success metrics of the product team: share of declined payments, time to the answer of the acquirer and the number of merchant support tickets.

## Success metrics

- Median time to the answer of the acquirer under two seconds.
- No change in the share of declined payments after a merchant moves.
- Fewer than five support tickets per hundred migrated merchants.

## Next steps

The product team will confirm the list of acquirers for the first wave, and the platform team will confirm the capacity plan. A decision on the status filter of the list endpoint is expected next month.
