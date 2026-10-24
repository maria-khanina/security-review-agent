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
AC-5. ⟦F3|The export is created by console-backend and the response returns its id and status.⟧

Security

AC-6. ⟦F1|A single read-write role covers every function of the back office.⟧
AC-7. ⟦F2|Logs can be queried by any service account in the cluster.⟧
AC-8. ⟦S:AUTH-03|A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use.⟧

⟦S:LOG-02|Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.⟧

⟦F4|Services call each other inside the cluster without credentials, because the namespace is isolated by the network policy.⟧
AC-9. ⟦S:AUTH-04|Administrative and back-office access requires multi-factor authentication.⟧
AC-10. ⟦S:AUTH-05|User passwords are stored only as salted argon2id or bcrypt hashes; reversible storage is prohibited.⟧
AC-11. ⟦S:AUTHZ-04|Administrative and debug endpoints are not reachable from the public internet.⟧
AC-12. ⟦S:CRYPTO-01|Personal data in our databases and object storage is encrypted at rest with AES-256, using keys held in the corporate key management service.⟧
AC-13. ⟦S:CRYPTO-05|Only approved algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are not.⟧
AC-14. ⟦S:CRYPTO-06|KMS holds the keys, the data stores only keep ciphertext, and key rotation happens at least yearly.⟧
AC-15. ⟦S:CRYPTO-07|Services validate TLS certificates and never disable verification.⟧
AC-16. ⟦S:SECRET-01|Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.⟧
AC-17. ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧
AC-18. ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧
AC-19. ⟦S:NET-04|Egress is limited to the approved list of third-party destinations.⟧
AC-20. ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are written to the logs.⟧
AC-21. ⟦S:DATA-03|Third parties receive only the fields they need, and only if an approved data processing agreement covers them.⟧
AC-22. ⟦S:DATA-04|Non-production environments contain no real personal or card data.⟧
AC-23. ⟦S:API-03|Webhook payloads are HMAC-signed and timestamped, and the receiver verifies the signature and the timestamp before accepting them.⟧
AC-24. ⟦S:API-05|We use parameterized queries only, with no SQL built from user input by string concatenation.⟧
AC-25. ⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧
AC-26. ⟦S:OPS-02|No container runs as root, and the root filesystem is read-only wherever possible.⟧

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
