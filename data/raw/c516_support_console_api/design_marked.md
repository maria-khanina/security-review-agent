# Support Console API - Design

## 1. Vision and scope

The Support Console API gives the support agents of Meridian Pay one place to look up customers, reset second factors, issue goodwill credits and answer the data requests of customers. The console turns the daily work of the agents from a set of manual tickets into a guided flow with a full record of every action. It is used by agents only, over the admin network.

## 2. Components

The Support web console talks to console-backend. console-backend validates the token of the agent with Keycloak, reads and writes customer profiles and action records in console-db (PostgreSQL), and records every action of an agent.

## 3. API

**GET /v1/customers** searches customers and returns id, full_name, email, phone_number and status for each match.

**GET /v1/customers/{customerId}** returns the profile with the same fields.

**POST /v1/customers/{customerId}/second-factor-reset** resets the second factor. The request has reason and ticket_id, and the response has id and status.

**POST /v1/customers/{customerId}/credits** issues a goodwill credit. The request has amount, currency, reason and ticket_id, and the response has id, amount, currency and status.

**GET /v1/agent-actions** lists the actions of the agents with id, agent_id, action and created_at.

**POST /v1/customers/{customerId}/data-export** exports the data held about a customer. The request has format and reason; the response has id, status and expires_at.

## 4. Customer data requests

The export call is the heart of the answer to the requests of customers to see their data. ⟦F1|The deadline for the answer is counted from the day the team has verified the identity of the customer and the scope of the request, which can take several weeks.⟧ Every request gets an entry in the request log of the console.

## 5. Storage of exports

The finished exports are prepared by the export vendor of the platform and offered for download for a limited time. ⟦F2|The vendor stores the files in a region chosen by the vendor.⟧ The agent sees only the expiry time of the link.

## 6. Delivery and change

The console is delivered through the pipeline of the platform team. ⟦S:PIP-02|Build artifacts are signed, and the signature is verified before deployment.⟧ ⟦S:CHG-02|Every change to production has a rollback plan that has been tested in a pre-production environment.⟧

## 7. Observability

Every request writes a structured log line with the agent, the action and the ticket. ⟦S:OBS-01|Traces and metrics do not contain personal data or card data.⟧ The dashboards show the number of lookups per agent, so that unusual volumes are visible.

## 8. Failure handling

When console-db is not reachable, the console shows a maintenance page and no action is possible. When Keycloak is not reachable, the agents cannot sign in, and sessions that exist end after their normal expiry.

## 9. Rollout

The console is introduced team by team, starting with the second-line support, and the old spreadsheet-based process is switched off a month after the last team.
