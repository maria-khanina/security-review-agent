# Support console API: design thread (pasted from #support-console)

**[09:12] nadia:** ok so for the doc. console-backend is the thing behind the Support web console. agents search customers, look at a profile, reset the 2nd factor, give goodwill credits, export the data of a customer. everything the agent does goes to agent_action in console-db (postgres)

**[09:14] jonas:** endpoints, quick: GET /v1/customers (id, full_name, email, phone_number, status), GET /v1/customers/{id}, POST /v1/customers/{id}/second-factor-reset (reason, ticket_id -> id, status), POST /v1/customers/{id}/credits (amount, currency, reason, ticket_id -> id, amount, currency, status), GET /v1/agent-actions (id, agent_id, action, created_at), POST /v1/customers/{id}/data-export (format, reason -> id, status, expires_at)

**[09:15] nadia:** yes. token check via keycloak, nothing new

**[09:21] jonas:** on the merchant side, agents of the merchant desk see only their merchants. ⟦F1|The tenant filter is added in the handlers for search and profile, and the other handlers rely on the caller to pass the right merchant.⟧

**[09:22] nadia:** hmm ok. TBD fix in v2?

**[09:24] priya:** also ⟦S:TEN-02|tenant data in console-db is separated by row-level security.⟧ and reversals / credits: ⟦S:PAY-02|refunds and reversals above 1,000 EUR need the approval of a second person, and the requester cannot approve their own.⟧

**[09:30] jonas:** attachments. agents add screenshots + pdfs to a case. ⟦S:UPL-01|uploads are limited to 10 MB and the file type is checked on the content against an allowed list, not on the name.⟧ ⟦S:UPL-02|every uploaded file is scanned for malware before any other user or service can open it.⟧

**[09:33] nadia:** web side: ⟦S:TPC-02|third-party scripts are not loaded into pages that handle card data or credentials.⟧ the console is one SPA

**[09:41] priya:** libs. ⟦S:TPC-01|every third-party SDK or library is approved before its first use and the list of approved components is reviewed every six months.⟧

**[09:44] jonas:** ops stuff: ⟦S:IR-01|alerts about repeated failed logins, privilege changes and access to card data reach the on-call engineer within 15 minutes.⟧ ⟦S:DR-01|console-db has point-in-time recovery on with seven days retention.⟧

**[09:50] nadia:** what happens when something goes wrong in prod. ⟦F2|console-backend runs as three instances, and whoever from the team notices a problem writes in the channel.⟧

**[09:52] priya:** rollout: pilot with two teams, then EU, then UK. old console read-only after

**[09:55] nadia:** data export stays downloadable 7 days? TBD legal

**[09:56] jonas:** ok good, I'll turn this into the doc page tomorrow
