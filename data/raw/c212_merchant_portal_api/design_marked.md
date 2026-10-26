# portal API v2 - notes for the platform folks

(context as in the v1 doc + the settlement thread, see PORTAL-77)

## Shape
- Portal Gateway -> portal-backend -> portal-db (PG). KC for tokens, nothing new there.
- endpoints: GET /v1/settlements (id, period, gross, fees, net), GET /v1/settlements/{id}, POST /v1/users (email, role -> id, email, role), PATCH /v1/users/{id}/role, POST /v1/reports (report_type, from_date, to_date -> id, status, expires_at), GET /v1/reports/{id}/download
- reports async, ready within minutes, expire after 7d

## Tenancy
- ⟦S:TEN-01|Every query on merchant data is filtered by the tenant id from the token, never by a request param.⟧
- ⟦F1|Tenant separation is described in the data model through the merchant_id column, but nothing in the database enforces it, the repository layer sets the filter.⟧
- TBD whether RLS goes in v2 or v3

## Uploads
- logo + CSV of users to invite (max 500 rows, TBD)
- ⟦S:UPL-01|Uploads are capped at 10 MB, and the file type is checked on the content against an allowed list, not on the name.⟧
- ⟦F3|portal-backend takes the file from the request, puts it into the object store under the merchant prefix and returns the id.⟧

## Pages
- ⟦S:TPC-02|No third-party scripts on the pages that handle card data or credentials.⟧
- ⟦S:DR-02|The recovery time objective of the service is 4 hours at most, and a failover exercise proves it at least once a year.⟧
- ⟦S:IR-02|A written runbook covers security incidents of the service, the on-call engineer can be paged around the clock, and a rehearsal takes place every six months.⟧
- web app is the usual Merchant web app, one SPA

## Ops
- ⟦F2|The alert rule for failed logins and privilege changes runs once a day, the result goes to the on-call channel with the daily summary.⟧
- ⟦S:DR-01|portal-db: PITR on, 7 days.⟧

## Rollout
- pilot with ~10 merchants for 2 weeks, then everybody
- feature flag per merchant, same flag service as settlements
- rollback = flag off, no data migration needed

## Known
- settlement period boundaries are UTC (finance wants local, PORTAL-91)
- role names differ between KC and the portal (viewer vs read_only), mapping table in portal-backend
