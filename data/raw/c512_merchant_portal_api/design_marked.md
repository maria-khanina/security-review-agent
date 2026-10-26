# merchant portal api - design thread (pasted from #portal-design)

**anna.k** ok so here is what we agreed, pasting so it does not get lost
**anna.k** merchant web app -> Portal Gateway -> portal-backend -> portal-db (postgres). Keycloak validates the tokens at the gateway
**dmitri** endpoints: GET /v1/settlements, GET /v1/settlements/{id}, POST /v1/users (email, role -> id, email, role), PATCH /v1/users/{id}/role, POST /v1/reports (report_type, from_date, to_date -> id, status, expires_at), GET /v1/reports/{id}/download
**dmitri** settlements return id, period, gross, fees, net
**anna.k** yes
**sam** about the data. ⟦S:RES-01|personal data of customers in the EU is stored and processed only in regions of the EU⟧ and for backups ⟦S:RES-02|backups and replicas of the personal data of customers in the EU stay in regions of the EU as well⟧
**sam** portal-db is in Frankfurt already (TBD replica in Dublin?)
**anna.k** ok
**lena** consent for the marketing mails of merchants: ⟦S:PRV-02|consent to marketing messages is recorded with its time and the version of the wording, and a withdrawal stops the messages within 24 hours⟧
**lena** that is the same as in the wallet
**dmitri** customer requests for their data? ⟦F2|portal-backend has the records of the merchant users, so those requests would end up there, I guess, somebody has to look at it (TBD)⟧

⟦S:OBS-02|The service reports a health check to the shared dashboard every minute and publishes the error rate per endpoint there.⟧
**anna.k** later
**sam** traces: ⟦S:OBS-01|traces and metrics do not contain personal data or card data⟧ (TBD check the gateway plugin config)
**lena** delivery. ⟦S:PIP-02|build artifacts are signed and the signature is verified before deployment⟧ and ⟦S:CHG-02|every change to production has a rollback plan that has been tested in a pre-production environment⟧
**dmitri** about review: ⟦F1|for the small changes we merge and deploy first and the review happens after the deploy, otherwise the reports fix takes days⟧

⟦S:PRV-03|Each use of customer data is tied to a purpose in the privacy notice shown at sign-up, and a new purpose needs a new notice and new consent.⟧
**lena** hmm
**dmitri** it is only for small ones
**sam** ⟦S:CAP-01|public endpoints answer HTTP 503 instead of queueing requests when their capacity is exhausted⟧ done in the gateway config
**anna.k** report not ready in 10 min -> failed, merchant asks again (TBD)
**anna.k** rollout: 10 merchants, a week, then all (TBD date)
**sam** open: who can download a report? (TBD) filters for settlements? (TBD)
