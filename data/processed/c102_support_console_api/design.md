SUP-512: Support Console API, account actions for support agents

Type: Epic
Priority: High
Component: Customer Operations
Reporter: operations lead
Assignee: console team

DESCRIPTION

As a support agent, I want to find a customer and perform the common account actions in one place, so that I can resolve a ticket without switching between tools.

SCOPE

Components: console-backend, console-db (PostgreSQL), Keycloak, Support web console.

Flow: the Support web console sends requests to console-backend. console-backend checks the agent's token with Keycloak and reads and writes console-db.

API (all under /v1):

- GET /v1/customers: search customers. Response items: id, full_name, email, phone_number, status.
- GET /v1/customers/{customerId}: retrieve a customer profile. Same fields.
- POST /v1/customers/{customerId}/second-factor-reset: reset the second factor of a customer. Request: reason, ticket_id. Response: id, status.
- POST /v1/customers/{customerId}/credits: issue a goodwill credit. Request: amount, currency, reason, ticket_id. Response: id, amount, currency, status.
- GET /v1/agent-actions: list actions taken by support agents. Response items: id, agent_id, action, created_at.
- POST /v1/customers/{customerId}/data-export: export the data held about a customer. Request: format, reason. Response: id, status, expires_at.

ACCEPTANCE CRITERIA

Functional

AC-1. A search returns at most fifty customers, newest contact first.
AC-2. A reset or a credit needs a ticket reference, and one ticket can be used for one credit only.
AC-3. Credits above the limit of the agent's group are marked pending until a team lead releases them.
AC-4. Every call that changes something writes a row to the agent action list.
AC-5. The export is created by console-backend and the response returns its id and status.

Security

AC-6. A single read-write role covers every function of the back office.
AC-7. Logs can be queried by any service account in the cluster.
AC-8. Access tokens expire within 15 minutes; refresh tokens are rotated on use.
AC-9. Administrative and back-office access requires multi-factor authentication.
AC-10. User passwords are stored only as salted argon2id or bcrypt hashes; reversible storage is prohibited.
AC-11. Administrative and debug endpoints are not reachable from the public internet.
AC-12. Personally identifiable information is encrypted at rest with AES-256.
AC-13. Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.
AC-14. Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.
AC-15. Services validate TLS certificates and never disable verification.
AC-16. Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.
AC-17. Runtime secrets are fetched from the approved secret store at startup.
AC-18. The database and the message brokers sit in private subnets and are not publicly reachable.
AC-19. Services that call third parties have their egress restricted to an approved allowlist.
AC-20. Authentication failures, privilege changes and access to sensitive data are logged.
AC-21. Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.
AC-22. Non-production environments do not contain real personal or card data.
AC-23. Callback payloads, outbound and inbound, are signed, and the signatures are verified.
AC-24. Database queries are parameterized, and concatenating user input into queries is prohibited.
AC-25. The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.
AC-26. Containers run as a non-root user, with a read-only root filesystem where possible.

DEFINITION OF DONE

- All acceptance criteria verified in staging with the three agent groups of the pilot.
- Dashboard with request rate, error rate and the number of pending credits.
- Runbook entry for an unreachable identity provider (TBD, owner: platform team).
- Agent handbook page updated with the new screens (TBD, owner: operations lead).

OUT OF SCOPE

- Customer self-service (SUP-498).
- Bulk actions on several customers (SUP-530).
- Changes to the ledger posting job (LED-77).

NOTES

The profile copies in console-db are refreshed hourly by the customer data team, so a search can show data that is up to an hour old.
