## Policy v1

- R13 (vague): Sensitive communications between internal components shall be protected in transit.
- R15 (vague): Cryptographic keys must be managed securely throughout their lifecycle in accordance with industry practice.
- R23 (vague): Logs should avoid recording sensitive data wherever practicable.
- R28 (vague): Personal data must be retained only for as long as is reasonably necessary and must be disposed of appropriately when it is no longer required.
- R35 (vague): This policy is reviewed annually and after any significant security incident.
- R36 (vague): Violations may result in disciplinary action in accordance with HR procedures.

Found 0.40 of the requirements to clarify, 0.67 of the listed ones are right.

## Policy v2

- R8 (vague): Internal users should be assigned roles appropriate to their job, and services should define role sets as needed.
- R9 (vague): Every service should connect to its database with a dedicated account that has only the grants it needs, and applications should avoid shared administrative credentials.
- R18 (vague): Legacy partner integrations may continue to use TLS 1.0 until a migration date is agreed with Security Architecture.
- R20 (vague): Each category of personal data should have a retention period, and an automated job should delete the data when the period ends.
- R23 (vague): Reports and exports containing personal data should be made available only to authorized users and for a limited time.
- R24 (vague): Logs should not contain secrets, card numbers or personal data other than opaque identifiers.
- R26 (vague): Secrets must not be stored in source code, configuration files, API specifications or infrastructure definitions.
- R33 (vague): Service credentials must be rotated periodically and after suspected exposure.
- R40 (vague): Audit logs must be stored in tamper-resistant storage and retained for an appropriate period.
- R41 (vague): Access to centralized logs should be restricted to personnel who need it.

Found 0.57 of the requirements to clarify, 0.40 of the listed ones are right.

## Policy v3

- R2 (vague): Services SHOULD authenticate each other with mutual TLS or workload identity tokens.
- R13 (vague): Internal traffic SHOULD be encrypted in transit.
- R17 (vague): Backups should be encrypted and restore procedures tested regularly.
- R18 (vague): Secrets MUST NOT be committed to code, configuration or specs.
- R21 (vague): Reporting replicas may be exposed through an allowlisted public endpoint when an external vendor requires it.
- R25 (vague): Containers SHOULD run as non-root.
- R28 (vague): Public APIs MUST be protected against excessive use.
- R31 (vague): Log authentication failures, privilege changes and sensitive data access.
- R32 (vague): Never log secrets, card numbers or personal data other than opaque ids.

Found 0.33 of the requirements to clarify, 0.33 of the listed ones are right.

## Policy v4

- R3 (vague): Payment amounts and currencies should be protected against tampering in a manner appropriate to the risk.
- R11 (vague): Services must maintain appropriate procedures for responding to security incidents.

Found 0.50 of the requirements to clarify, 1.00 of the listed ones are right.

## Policy v5

- R3 (vague): Personal data should be used only for purposes that have been described to customers in an appropriate manner.
- R12 (vague): Every service should publish health checks and error rates to the shared dashboard in an appropriate way.

Found 0.50 of the requirements to clarify, 1.00 of the listed ones are right.
