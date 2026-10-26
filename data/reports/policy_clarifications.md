## Policy v1

- R9 (contradictory): Access rights to production systems must be reviewed at least quarterly by the system owner.
- R13 (vague): Sensitive communications between internal components shall be protected in transit.
- R15 (vague): Cryptographic keys must be managed securely throughout their lifecycle in accordance with industry practice.
- R23 (vague): Logs should avoid recording sensitive data wherever practicable.
- R24 (contradictory): Audit logs must be tamper-evident and retained for at least one year.
- R26 (contradictory): Audit logs older than 90 days may be archived or deleted by the owning team.
- R28 (vague): Personal data must be retained only for as long as is reasonably necessary and must be disposed of appropriately when it is no longer required.
- R35 (contradictory): This policy is reviewed annually and after any significant security incident.

Found 0.60 of the requirements to clarify, 0.75 of the listed ones are right.

## Policy v2

- R3 (contradictory): Access tokens must expire within 15 minutes, and refresh tokens must be rotated every time they are used.
- R8 (vague): Internal users should be assigned roles appropriate to their job, and services should define role sets as needed.
- R13 (contradictory): All external network traffic must use TLS 1.2 or higher, and plain HTTP listeners are not permitted.
- R18 (contradictory): Legacy partner integrations may continue to use TLS 1.0 until a migration date is agreed with Security Architecture.
- R33 (contradictory): Service credentials must be rotated periodically and after suspected exposure.
- R34 (contradictory): Databases and message brokers must run in private subnets and must not have public endpoints.
- R36 (contradictory): SSH, RDP and database ports must not be open to 0.0.0.0/0.
- R40 (vague): Audit logs must be stored in tamper-resistant storage and retained for an appropriate period.

Found 0.71 of the requirements to clarify, 0.62 of the listed ones are right.

## Policy v3

- R3 (contradictory): Access tokens MUST expire within 15 minutes. Refresh tokens MUST be rotated on use.
- R7 (contradictory): Admin and debug endpoints MUST NOT be exposed to the public internet.
- R8 (contradictory): For long-lived sessions, an access token lifetime of up to 30 minutes is acceptable.
- R9 (contradictory): Personal data at rest MUST be encrypted with AES-256.
- R10 (contradictory): Card numbers MUST NOT be stored. Use tokens from the card token vault.
- R11 (contradictory): External traffic MUST use TLS 1.2 or higher.
- R12 (contradictory): Legacy partner endpoints may use TLS 1.0 until they have migrated.
- R17 (contradictory): Backups should be encrypted and restore procedures tested regularly.
- R18 (vague): Secrets MUST NOT be committed to code, configuration or specs.
- R21 (contradictory): Reporting replicas may be exposed through an allowlisted public endpoint when an external vendor requires it.
- R31 (vague): Log authentication failures, privilege changes and sensitive data access.
- R32 (contradictory): Never log secrets, card numbers or personal data other than opaque ids.

Found 0.67 of the requirements to clarify, 0.50 of the listed ones are right.

## Policy v4

- R3 (vague): Payment amounts and currencies should be protected against tampering in a manner appropriate to the risk.
- R10 (contradictory): Alerts about repeated failed logins, privilege changes and access to card data must reach the on-call engineer within 15 minutes.
- R11 (contradictory): Services must maintain appropriate procedures for responding to security incidents.
- R14 (contradictory): Databases must have point-in-time recovery enabled with at least seven days of retention.
- R15 (contradictory): The recovery time objective of a critical service must not exceed 4 hours, and it must be proven by a failover exercise at least once a year.
- R16 (contradictory): For batch services a recovery time objective of up to 24 hours is acceptable.

Found 1.00 of the requirements to clarify, 0.67 of the listed ones are right.

## Policy v5

- R6 (contradictory): Every change to production must be reviewed by a second engineer before it is deployed.
- R7 (contradictory): Emergency changes may be deployed without a prior review and must be reviewed within 24 hours after the deployment.

Found 0.50 of the requirements to clarify, 1.00 of the listed ones are right.
