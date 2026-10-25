# Merchant Portal API - Design

## 1. Overview

The Merchant Portal API is the back-office interface of Meridian Pay for merchants. Merchants use it to view their settlements, manage the users of their account and download reports. The API is called by the Merchant web app through the Portal Gateway. This design was prepared on the basis of the Payment Gateway design and the Wallet Service design, and the text of the sections on operation was taken over from there.

## 2. Components

| Component | Role |
|---|---|
| Portal Gateway | Entry point, validates tokens with Keycloak |
| portal-backend | Business logic for settlements, users and reports |
| portal-db (PostgreSQL) | Settlements and merchant users |
| Keycloak | Identity provider for merchant users |
| Merchant web app | Browser client of the merchants |

The Payments Edge Gateway forwards authenticated requests to portal-backend. (See also section 6 of the Wallet Service design.)

## 3. Endpoints

### 3.1 Settlements

**GET /v1/settlements** lists the settlements of the merchant. Each item has id, period, gross, fees and net.

**GET /v1/settlements/{settlementId}** returns one settlement with the same fields.

### 3.2 Users

**POST /v1/users** invites a merchant user. The request has email and role, the response has id, email and role.

**PATCH /v1/users/{userId}/role** changes the role of the user. The request has role, the response has id, email and role.

### 3.3 Reports

**POST /v1/reports** requests a transaction report. The request has report_type, from_date and to_date; the response has id, status and expires_at.

**GET /v1/reports/{reportId}/download** downloads a finished report. The response has id, status and expires_at.

## 4. Data location

Personal data of customers in the EU is stored and processed only in regions of the EU. portal-db lives in the Frankfurt region. Backups and replicas of the personal data of customers in the EU stay in regions of the EU as well.

## 5. Consent

The wallet app shows a text of the consent for marketing messages. When the legal team changes the consent text, the new text replaces the old one in the configuration, and the earlier versions are not kept. (TBD: move the text to the content system.)

## 6. Delivery

The delivery is done by the pipeline of the platform team. Credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour. Build artifacts are signed, and the signature is verified before deployment. Every change to production has a rollback plan that has been tested in a pre-production environment.

## 7. Observability

portal-backend and the gateway write structured logs. Traces and metrics do not contain personal data or card data. The dashboards show the latency and the error rate for each endpoint.

## 8. Behaviour under load

Load shedding exists for the payment endpoint only; all other endpoints of the gateway queue requests when the capacity is exhausted. The team measures the queue time of the report requests (TBD: limit).

## 9. Failure handling

A report that cannot be finished within ten minutes gets the status `failed`, and the merchant can request it again. If Keycloak is not reachable, the Portal Gateway rejects all requests with HTTP 503 and the web app shows a maintenance message.

## 10. Rollout

The portal goes live for ten merchants first. After one week without incidents all merchants are moved. The old merchant dashboard of the monolith is switched off one month later.

## 11. Open questions

- Whether the report download is limited to the user who requested the report.
- Whether the settlement list gets filters by period (TBD).
