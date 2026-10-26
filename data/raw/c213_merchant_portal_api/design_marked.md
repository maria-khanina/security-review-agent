# Merchant Portal API: the self-service platform for merchants

## Vision

The Merchant Portal API gives every merchant a complete self-service experience: settlements, team management and reporting, all in one place. Merchants see every settlement as soon as it is closed, invite colleagues in seconds, and download any report they need without contacting support. The portal also predicts cash flow for the next thirty days and suggests the best payout schedule for each business.

## Architecture

The Merchant web app talks to the Portal Gateway. ⟦F2|The Portal Gateway is the single front door of the portal; it validates the token of every request with Keycloak and passes the request on to portal-backend, which holds the logic and reads portal-db (PostgreSQL).⟧ The portal-backend computes the settlement views, manages the merchant users and creates the reports in the background.

⟦S:DR-02|Recovery of the service is required within 4 hours, which is demonstrated by an annual failover exercise.⟧

## Endpoints

- **GET /v1/settlements** lists the settlements with id, period, gross, fees and net, and filters them by period.
- **GET /v1/settlements/{settlementId}** returns one settlement with the same fields.
- **POST /v1/users** invites a colleague with an email and a role, and returns the id, the email and the role.
- **PATCH /v1/users/{userId}/role** changes the role of a user and returns the id, the email and the role.
- **POST /v1/reports** creates a report of a chosen type for a date range, and returns the id, the status and the expiry time. The report is ready within a minute for the typical merchant.
- **GET /v1/reports/{reportId}/download** downloads the finished report.

## Merchant data

The portal is multi-tenant: all merchants share one set of tables, and each merchant sees only its own data. ⟦S:TEN-01|Each query on merchant data is filtered by the tenant identifier taken from the authenticated token and never from a request parameter.⟧ ⟦S:TEN-02|Row-level security separates the tenants in portal-db, so the database itself keeps the rows of one merchant away from the others.⟧

## Files

Merchants upload a company logo for the reports and a CSV file with the colleagues to invite. ⟦S:UPL-02|Every uploaded file is scanned for malware before any other user or service can open it.⟧ The logo appears on every report within seconds after the upload.

## Reliability

The portal is designed for the availability that merchants expect from a payment platform. ⟦F1|Point-in-time recovery is not enabled for portal-db, and only a nightly snapshot exists, which is considered enough for a back-office portal.⟧ The portal-backend runs in three replicas, and a failed replica is replaced automatically.

## Reports

The report types are `transactions`, `settlements` and `fees`. A report covers at most thirteen months and is available for download for seven days. Merchants can schedule a report to run every week; the finished report appears in the portal and an email with a link is sent to the person who scheduled it.

## Roadmap

The first release delivers settlements and users. Reports follow in the second release, and cash-flow predictions in the third. The portal already supports the three releases in the same codebase, and the feature flags decide which merchants see which functions.

## Success measures

- Fewer than five percent of merchants contact support about settlements.
- Seventy percent of the invited colleagues activate their account in the first week.
- The median time to produce a report stays below one minute.
