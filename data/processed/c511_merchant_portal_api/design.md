# Merchant Portal API

## Components

| Component | Type | Notes |
|---|---|---|
| Portal Gateway | api_gateway | TLS termination, token validation via Keycloak |
| portal-backend | service | settlements, users, reports |
| portal-db (PostgreSQL)| | database | settlements, merchant users, report metadata |
| Keycloak | identity_provider | merchant user login |
| Merchant web app | client_app | browser |

## Endpoints

| Method | Path | Request | Response |
|---|---|---|---|
| GET | /v1/settlements | - | id, period, gross, fees, net |
| GET | /v1/settlements/{settlementId} | - | id, period, gross, fees, net |
| POST | /v1/users | email, role | id, email, role |
| PATCH | /v1/users/{userId}/role | role | id, email, role |
| POST | /v1/reports | report_type, from_date, to_date | id, status, expires_at |
| GET | /v1/reports/{reportId}/download | - | id, status, expires_at

## Controls

| Area | Control |
|---|---|
| Customer rights | Requests of customers to see or delete their personal data are answered within 30 days and recorded in the request register. |
| Consent | Consent to marketing messages is recorded with its time and the version of the wording, and a withdrawal stops the messages within 24 hours. |
| Change | Every change to production has a rollback plan that has been tested in a pre-production environment. |
| Pipeline credentials | Credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour. |
| Traces | Traces and metrics do not contain personal data or card data.
| Capacity | Public endpoints answer HTTP 503 instead of queueing requests when their capacity is exhausted. |

## Delivery

| Step | Where | Artifact |
|---|---|---|
| build | build server | portal-backend image |
| deploy | production | copied from the build server to production by a script, no signature is created or checked|
| verify | production | smoke test of GET /v1/settlements |

## Failure

| Event | Result |
|---|---|
| report not ready in 10 min | status failed, merchant requests again |
| Keycloak down | HTTP 503 from Portal Gateway |

## Open

| Item | Owner |
|---|---|
| filter settlements by period | TBD |
| limit report download to requester | TBD |
