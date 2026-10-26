# Support Console API

## Overview (written by Mara)

The Support Console API is the back-office API behind the Support web console. Support agents use it to look up customers, reset the second factor of a customer, issue goodwill credits, reverse fees and export the data that Meridian Pay holds about a customer. Every action of an agent is written to an action record, so that the team leads can see who did what.

## Components

The Support web console calls console-backend. console-backend validates the token of the agent with Keycloak, reads and writes console-db (PostgreSQL) with the customer profiles and the agent action records.

## Endpoints

- `GET /v1/customers` - search customers, returns id, full_name, email, phone_number, status
- `GET /v1/customers/{customerId}` - one customer profile, same fields
- `POST /v1/customers/{customerId}/second-factor-reset` - request: reason, ticket_id; response: id, status
- `POST /v1/customers/{customerId}/credits` - request: amount, currency, reason, ticket_id; response: id, amount, currency, status
- `GET /v1/agent-actions` - list of actions, with id, agent_id, action, created_at
- `POST /v1/customers/{customerId}/data-export` - request: format, reason; response: id, status, expires_at

### Credits and reversals (Mara)

A goodwill credit pays an amount to the wallet of the customer. A fee reversal gives back a fee that was taken from the customer. ⟦F2|Reversals and credits above 1,000 EUR are approved by the team lead, and the approval is written into a spreadsheet of the team; the console does not check the approval.⟧ The ticket_id of the request has to point to a ticket in the support tool.

⟦S:IR-02|A written runbook covers security incidents of the service, the on-call engineer can be paged around the clock, and a rehearsal takes place every six months.⟧

---

# Part 2: Technical notes (Dmitri)

## console-backend and the DB

console-backend is a stateless service, three instances. Tabs in the console map 1:1 on the endpoints above. console-db (Postgres) has two groups of tables: customer_profile (copy of the profile, refreshed every night) and agent_action (append only).

### Tenant / merchant scope

⟦S:TEN-01|Every query on merchant data is filtered by the tenant identifier taken from the authenticated token and never by a request parameter.⟧ Agents of the merchant support team get merchant data only for merchants that are assigned to them.

### Attachments

Agents can attach screenshots and PDF files to a case (TBD max count). ⟦F1|Attached files are checked by the antivirus on the laptop of the agent who downloads them, the console itself does not scan them.⟧

### Web pages

⟦S:TPC-02|Third-party scripts are not loaded into the pages that handle card data or credentials.⟧ The new console is a single-page app built from our own components.

### Alerting and recovery

⟦S:IR-01|Alerts about repeated failed logins, privilege changes and access to card data reach the on-call engineer within 15 minutes.⟧ ⟦S:DR-01|console-db has point-in-time recovery enabled with seven days of retention.⟧

### Libraries

⟦S:TPC-01|Every third-party SDK or library is approved before its first use, and the list of approved components is reviewed every six months.⟧

## Rollout

Week 1: two pilot teams. Week 2-3: all agents of the EU teams. Week 4: UK teams. The old console is read-only after week 4 and is switched off after another month.

## Open

- credit limits per agent role (TBD)
- how long data exports stay downloadable (seven days now, legal wants to confirm)
