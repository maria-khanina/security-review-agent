# Card Token Vault - Design Description

## 1. Purpose and scope

This document describes the Card Token Vault of Meridian Pay in accordance with company policy and the applicable standards for the protection of card data. The vault replaces the primary account number of a card by a token for all services of the platform and returns the number to the authorized components when a payment needs it. The service is internal and is reachable from the vault private subnet only.

## 2. Components

- **tokenization-service** implements the tokenization and detokenization of card numbers.
- **vault-db (PostgreSQL)** holds the card data in the form in which it is stored.
- **Vault and KMS** supply the data keys on request of tokenization-service.
- **vault private subnet** contains the components and is separated from the other networks of the company.

## 3. Functions

The vault offers two functions. Tokenization receives a primary account number from a payment service and returns a token. Detokenization receives a token from an authorized component and returns the number. Both functions are called over the private network, and the calls are recorded in the audit log group of the vault.

## 4. Operation

### 4.1 Delivery

The service is delivered by the pipeline of the platform team in accordance with company policy. ⟦S:PIP-01|Credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour.⟧ ⟦S:PIP-02|Build artifacts are signed, and the signature is verified before deployment.⟧

### 4.2 Change

⟦S:CHG-02|Every change to production has a rollback plan that has been tested in a pre-production environment.⟧ ⟦F2|Engineers who are confident in their change deploy it to production themselves, without waiting for the approval of the change board.⟧

⟦S:OBS-02|The shared dashboard polls the health check of the service once a minute and charts the error rate, with an alert when it exceeds 2% for five minutes.⟧

⟦S:PRV-03|Each use of customer data is tied to a purpose in the privacy notice shown at sign-up, and a new purpose needs a new notice and new consent.⟧

### 4.3 Diagnostics

For the analysis of difficult faults the operations team may enable more detailed tracing. ⟦F1|Debug traces with the full payloads of the requests are switched on in production for a few services of the platform, among them the callers of the vault.⟧ The setting is reviewed at the end of each quarter.

## 5. Failure modes

If Vault and KMS is not reachable, the service answers with an error, and the calling payment service retries after a pause. If vault-db is not reachable, the same applies. The service keeps no card number in memory beyond the duration of a request.

## 6. Rollout

The vault is introduced service by service: the checkout first, the refund service second and the remaining payment services afterwards. The direct storage of card numbers in the payment database is removed after the last service has moved.

## 7. Roles

The platform team owns the vault and its on-call. The payment teams are the consumers of the tokens.
