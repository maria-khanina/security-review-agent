# Support Console API: Architecture Description

Author: Platform Architecture (Hannah W.)
Version: 0.9, for review
Supersedes: the "Agent Toolbox" note (link to the old wiki no longer resolves)

## 1. Summary

The Support Console API is the server side of the tool that customer support agents use all day. It lets an agent find a customer, look at the profile, reset the customer's second factor, grant a goodwill credit, export the data held about a customer when a data request arrives, and review what colleagues have done. This document explains how the Service is built and why, in enough detail for a new engineer to take it over.

## 2. Problem statement

Today an agent needs five browser tabs to handle one ordinary ticket. Profile data comes from one tool, resets from another, credits are noted in a shared spreadsheet, and exports are requested by e-mail to the data team. This causes three problems that the business has measured: handling time is high, mistakes happen when an agent copies an identifier from one tab to another, and nobody can answer quickly what a particular agent did on a particular day. The Service removes the tabs and puts every action behind one API with one record of actions.

## 3. Components

- **Support web console.** The browser application. It holds no business logic and calls the API for everything.
- **console-backend.** The service that implements the API. It is stateless, runs as three replicas and is configured through environment variables that name the other components.
- **console-db (PostgreSQL).** The store of the Service. It keeps a copy of the customer profile fields the agents need, the record of every action an agent took, and the state of export jobs.
- **Keycloak.** The identity provider. The console sends the agent to Keycloak to sign in and then presents the token it receives to console-backend.

Flows: the console talks to console-backend; console-backend validates tokens with Keycloak; console-backend reads and writes console-db. There are no other flows. In particular, console-backend does not call the payment ledger directly. Credits are written to a table in console-db and a separate job posts them to the ledger.

## 4. The API

All paths start with /v1.

1. GET /v1/customers searches customers by e-mail, phone number or name. Each result has id, full_name, email, phone_number and status.
2. GET /v1/customers/{customerId} returns the same fields for one customer.
3. POST /v1/customers/{customerId}/second-factor-reset starts a reset of the second factor. The request has a reason and a ticket_id. The response has an id and a status.
4. POST /v1/customers/{customerId}/credits grants a goodwill credit. The request has amount, currency, reason and ticket_id. The response has id, amount, currency and status.
5. GET /v1/agent-actions lists actions with id, agent_id, action and created_at; team leads use it for the weekly review.
6. POST /v1/customers/{customerId}/data-export creates an export of the data held about a customer. The request has a format and a reason. The response has an id, a status and an expires_at.

## 5. Data model

console-db has four main tables. The first, customer_copy, holds the profile fields listed above plus a refreshed_at timestamp. The second, agent_action, holds one row for every call that changes something, with the agent id, the action name, the customer id, the ticket reference and the time. The third, credit_request, holds the credits waiting to be posted to the ledger. The fourth, export_job, holds the state of data exports. ⟦F2|console-backend reads and writes these tables in console-db (PostgreSQL) for every request that it handles.⟧

Customer copies are refreshed from the customer database every hour by a job owned by the customer data team. A search may therefore show data that is up to an hour old, and the console displays the refresh time next to every profile so that an agent can judge whether to check the source.

## 6. Behavior in detail

Reset flow: the agent opens the profile, selects reset, enters the ticket reference and a reason. The API checks that the ticket exists and belongs to this customer, writes the request to agent_action, and starts the reset through the identity provider. The customer then receives an e-mail with a link that is valid for a short time. The status in the response moves from pending to completed when the customer has finished.

Credit flow: the API checks the amount against the limit for the agent's group. Amounts at or below the limit become credit requests immediately. Amounts above the limit wait until a team lead releases them. A ticket can be used for one credit only. The ledger job picks up credit requests every five minutes.

Export flow: an export is requested together with the reason, usually a data request from the customer. The job collects the data from the customer database and the ledger and writes the file. The response shows the status of the job. Exports are rarely requested, around twenty a week.

## 7. Security design

7.1 Sessions and tokens. ⟦F1|The lifetime of an access token is configurable per client application, and for the support console it is set to thirty days so that agents are not interrupted by a new sign-in during a shift change.⟧

7.2 Passwords and cryptography. ⟦S:AUTH-05|User passwords are stored only as salted argon2id or bcrypt hashes; reversible storage of passwords is prohibited.⟧ ⟦S:CRYPTO-01|Personally identifiable information is encrypted at rest with AES-256.⟧ ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧

7.3 Administrative surface. ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧

7.4 Secrets. ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧ Rotation of those secrets is still to be decided (TBD with the platform team).

7.5 Logging. ⟦F3|Authentication failures are not written to the log, in order to keep the volume of the log small.⟧ ⟦S:LOG-02|Logs contain no secrets, card numbers or personal data beyond opaque identifiers.⟧

7.6 Data protection. ⟦S:DATA-02|Personal data has a defined retention period and is deleted when it expires or on a verified request from the data subject.⟧ ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧

7.7 Application and delivery. ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧ ⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧

## 8. Failure handling

When Keycloak is unreachable, console-backend answers write requests with a clear error and keeps serving reads for tokens that were already validated. When console-db is unreachable, the API returns an error and the console tells the agent that the action was not recorded and must be repeated. A credit request that is accepted by console-backend but later rejected by the ledger job is shown in the agent's list with status failed and an explanation, and the agent can try again with a new ticket reference.

## 9. Capacity

About one hundred and twenty agents use the console during a day, and the busiest hour sees around two thousand API calls. The Service is sized for ten times that load. Searches are the most expensive operation; they use an index on the e-mail, the phone number and the normalized name, and they return at most fifty results.

## 10. Rollout and open points

The rollout is gradual: one agent group first, then all groups, then the old tools become read-only. Open points: the credit limits per group (TBD with Finance), the wording of the e-mail sent after a reset, and whether team leads should be able to export the agent action list as a file (TBD with the operations lead).
