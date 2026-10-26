# Support Console API - Design and Security Concept

## 1. Introduction

This document describes the Support Console API of Meridian Pay and, in a dedicated section, its security concept. The API is used by support agents to look up customers, reset second factors, issue goodwill credits, read the log of agent actions and export the data held about a customer. It is reachable from the admin network only.

## 2. Architecture

The Support web console is the browser client of the agent. console-backend is the service that implements the API. It validates the token of the agent with Keycloak and keeps customer profiles and agent action records in console-db (PostgreSQL).

## 3. API

- **GET /v1/customers** and **GET /v1/customers/{customerId}** return id, full_name, email, phone_number and status.
- **POST /v1/customers/{customerId}/second-factor-reset** takes reason and ticket_id and returns id and status.
- **POST /v1/customers/{customerId}/credits** takes amount, currency, reason and ticket_id and returns id, amount, currency and status.
- **GET /v1/agent-actions** returns id, agent_id, action and created_at.
- **POST /v1/customers/{customerId}/data-export** takes format and reason and returns id, status and expires_at.

## 4. Security concept

### 4.1 Perimeter

The console is protected by the admin network zone and by the single sign-on of the company. Access from outside this zone is not possible. The concept follows the principle of defence in depth and the zero-trust model of the platform (the second is a goal for the next year).

### 4.2 Identity and access

Every agent signs in with Keycloak. Roles are assigned per team: first line can search and read, second line can reset factors, and only team leads can issue credits above the limit of the team (the final limits are TBD).

### 4.3 Data location

⟦S:RES-01|Personal data of customers in the EU is stored and processed only in regions of the EU.⟧ console-db runs in the Frankfurt region and the export files are created there. ⟦S:RES-02|Backups and replicas of the personal data of customers in the EU stay in regions of the EU as well.⟧

⟦S:CHG-01|Production changes need a review by a second engineer before they go live.⟧

### 4.4 Supply chain

console-backend is delivered through the platform pipeline, which produces the container image and runs the vulnerability scan. ⟦F2|The image of console-backend is built by the pipeline and rolled out to the cluster by the deployment job.⟧ The base image is updated every month by the platform team.

⟦S:OBS-02|The service reports a health check to the shared dashboard every minute and publishes the error rate per endpoint there.⟧

⟦S:PRV-03|The purposes of personal data are listed in the privacy notice that customers accept at sign-up, and the data is not used for any purpose outside that list.⟧

### 4.5 Change management

⟦S:CHG-02|Every change to production has a rollback plan that has been tested in a pre-production environment.⟧ The plan is attached to the change ticket and approved by the team lead.

### 4.6 Logging and monitoring

⟦F1|Error traces of console-backend include the request that failed, with all its fields, and the card number that did not pass the validation when a credit is booked to a card.⟧ The traces are kept for 30 days. The log of agent actions is append-only and is read through GET /v1/agent-actions.

### 4.7 Incident response

Suspicious volumes of lookups raise an alert to the security team (TBD threshold). The runbook for compromised agent accounts is kept by the security team.

## 5. Failure handling

When console-db is not reachable, the console shows a maintenance page and no action is possible. When Keycloak is not reachable, new sign-ins fail and existing sessions end at their normal expiry.

## 6. Rollout

The console is introduced team by team, starting with the second line. The spreadsheet process stays available for one month after the last team (TBD date).
