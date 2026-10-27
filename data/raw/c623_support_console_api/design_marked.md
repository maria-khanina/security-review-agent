Support Console API - design (ESL, sorry for my English)

1. What is this
This is back office API for the support agents. The agents use the Support web console. The console call the console-backend service. The backend read and write console-db (PostgreSQL). Login is by Keycloak.

2. Endpoints
- GET /v1/customers - search the customers
- GET /v1/customers/{customerId} - show profile of one customer
- POST /v1/customers/{customerId}/second-factor-reset - reset second factor of customer
- POST /v1/customers/{customerId}/credits - give a goodwill credit

3. How the credit work
Agent can give a goodwill credit up to 50 EUR. Credit above this need second agent. The backend write a line to the table `credits` with agent, customer, amount and reason.

4. Exports
Agents can export lists of customers for the campaign team. ⟦F1|Exports of up to 100,000 records are not approved by anyone because the data are pseudonymised.⟧ ⟦F3|The download link of an export never expires, the campaign team can use it again.⟧

5. Testing
⟦F2|For the acceptance tests we use a sample of 1,000 real customers.⟧

6. Rules
- ⟦S:ARC-02|Documents uploaded by customers are deleted within 30 days after the account is closed.⟧
- ⟦S:VUL-01|Critical vulnerabilities are fixed in production within 7 days after they are published.⟧
- ⟦S:VUL-02|Third-party components are not more than two major versions behind the latest release and the service register show the version of each.⟧
- ⟦S:TST-02|Test accounts in production are removed within 7 days after the test ends.⟧
- ⟦S:MON-01|Alerts of severity high are acknowledged within 15 minutes.⟧

7. TBD
How many agents can be logged in at same time?
