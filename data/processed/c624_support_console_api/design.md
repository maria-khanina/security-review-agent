support console api - how it's done (what I remember, ask me if unsure)

The support web console talks to console-backend (it is the service), backend uses console-db (PostgreSQL), login is Keycloak.

Endpoints, you know them: GET /v1/customers, GET /v1/customers/{customerId}, POST /v1/customers/{customerId}/second-factor-reset, POST /v1/customers/{customerId}/credits.

Credits: up to 50 EUR alone, above that a second agent. Written to `credits`.

Second factor reset: agent asks the customer 3 questions, then the button. The customer gets a message.

Load test (last year, Pieter): we used production exports to load test the reporting module of the console, the files were deleted after the test, I think.

Partners: The console sends events about credits to the finance partner Tallyo for their books, it is not in the register because it was added after the register was filled in.

Test accounts: Test accounts in production are disabled when the test is over, they are not deleted.

The rest is the usual stuff:
- Documents uploaded by customers are deleted within 30 days after the account is closed.
- Critical vulnerabilities are fixed in production within 7 days after publication.
- Exported files with personal data are encrypted and deleted from the download location after 7 days.
- Owner and deputy are named in the service register.
- High alerts are acknowledged within 15 minutes.
