# Support Console API: Design and Control Statement

Owner: Customer Operations Engineering
Status: Approved for implementation, subject to annual review
Applicable framework: Meridian Pay Information Security Policy v4.2

## 1. Purpose

This document describes the Support Console API ("the Service"), the back-office interface through which support agents of Meridian Pay look up customers, reset a customer's second factor and issue goodwill credits. It records the functional design and, in accordance with company policy, the controls under which the Service operates. The audience is the Security Architecture group, the Data Protection Officer and the engineers who will maintain the Service.

## 2. Context and goals

Support agents currently work from several internal tools that were never designed to be used together. The goals of the Service are to give agents one consistent interface for the five most frequent account actions, to give team leads a reliable record of what each agent did, and to retire the spreadsheets in which agents note credits today. The Service is used only by employees; customers never call it.

Non-goals: customer self-service, bulk operations on more than one customer, and any change to the payment ledger itself. Credits issued through the Service are posted to the ledger by an existing job that this document does not change.

## 3. Architecture

The Service consists of the following components, deployed in the support private subnet:

- the Support web console, the browser application the agents use;
- console-backend, the service that implements the API;
- console-db (PostgreSQL), which holds customer profile copies and the record of agent actions;
- Keycloak, the identity provider that issues the tokens the Service accepts.

The web console sends requests to console-backend. console-backend validates the agent's token against Keycloak and reads and writes console-db. ⟦F2|console-backend writes an audit entry for every account action that an agent performs and passes the entry on to the central logging pipeline.⟧

## 4. Endpoints

The API has six operations.

- GET /v1/customers searches customers. The response lists id, full_name, email, phone_number and status for each match.
- GET /v1/customers/{customerId} returns the same fields for one customer.
- POST /v1/customers/{customerId}/second-factor-reset resets the second factor of a customer. The request carries a reason and a ticket_id; the response returns an id and a status.
- POST /v1/customers/{customerId}/credits issues a goodwill credit. The request carries amount, currency, reason and ticket_id; the response returns id, amount, currency and status.
- GET /v1/agent-actions lists the actions taken by agents, with id, agent_id, action and created_at.
- POST /v1/customers/{customerId}/data-export exports the data held about a customer. The request carries a format and a reason; the response returns an id, a status and an expires_at.

## 5. Behavior

A reset or a credit requires a ticket reference, and the same ticket cannot be used for two credits. Credits above the limit that a team lead sets for each agent group are not rejected but are marked pending, and a team lead releases them. Searches return at most fifty customers, ordered by the last contact. Customer profile copies in console-db are refreshed from the customer database every hour, so an agent may see data that is up to one hour old.

## 6. Control statements

6.1 Identity. ⟦F1|Multi-factor authentication for administrative accounts is scheduled for a later release, and until then the administrative accounts sign in with a password only.⟧ ⟦S:AUTH-05|User passwords are stored only as salted argon2id or bcrypt hashes, and reversible storage of passwords is prohibited.⟧

6.2 Access. ⟦S:AUTHZ-02|Internal users receive only the roles required for their job, and roles are defined per service.⟧ ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧ ⟦S:AUTHZ-05|Access rights to production systems are reviewed at least quarterly.⟧ ⟦F3|All state-changing operations require an authenticated caller.⟧

6.3 Cryptography. ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧ ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧

6.4 Secrets and network. ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧

6.5 Logging. ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧

6.6 Data. ⟦S:DATA-01|Only the personal data needed for the purpose is collected and stored.⟧ ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧ ⟦S:DATA-05|Data exports require authorization, are encrypted, and expire after a limited time.⟧

6.7 Application. ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧

For completeness it is noted that the retention period of customer profile copies in console-db is set by the Data Protection Officer and that the copies are deleted when it ends. The detailed control descriptions are maintained in the Access Standard (section 9, link no longer available).

## 7. Failure modes

If Keycloak is unreachable, the console shows a banner and read operations continue for agents who already hold a valid token; write operations are refused. If console-db is unavailable, the console shows an error page and no action is recorded. A credit that fails after the ledger job has accepted it is reconciled by the daily settlement comparison, and the agent is notified by e-mail.

## 8. Rollout

The Service is released to one agent group in the first month, to all groups in the second month, and the old spreadsheets are switched to read-only in the third month. Metrics tracked during the rollout are the median handling time of a reset, the share of credits marked pending, and the number of agent complaints per week.

## 9. Open points

The limit above which credits are marked pending is being agreed with Finance. The wording of the confirmation message shown to the customer after a reset is being agreed with the Customer Communications team.
