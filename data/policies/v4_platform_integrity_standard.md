# Meridian Pay Platform Integrity and Resilience Standard

This standard sets the controls for payment operations, merchant data, files, mobile apps, incident handling, third-party components and recovery. Each requirement is numbered so that audit findings can cite it. Where a requirement says "must", deviation needs an approved exception.

# Section PIR-1: Payment Operations

PIR-1.1 Every payment operation request (authorize, capture, refund or reversal) must carry an idempotency key, and a repeated key must return the original result without repeating the operation. PIR-1.2 Refunds and reversals above 1,000 EUR must be approved by a second person, and the person who requested the operation must not be able to approve it. PIR-1.3 Payment amounts and currencies should be protected against tampering in a manner appropriate to the risk.

# Section PIR-2: Merchant Tenancy

PIR-2.1 Every query on merchant data must be filtered by the tenant identifier taken from the authenticated token and never from a request parameter. PIR-2.2 Tenant data in shared storage should be separated by row-level security or by tenant-specific encryption keys.

# Section PIR-3: Uploaded Files

PIR-3.1 Uploaded files must not exceed 10 MB, and their type must be checked against an allowed list on the content of the file, not on its name. PIR-3.2 Uploaded files must be scanned for malware before any other user or service can open them.

# Section PIR-4: Mobile Apps

PIR-4.1 Mobile apps must pin the public key or the certificate of the Meridian Pay API and must refuse connections that fail the check. PIR-4.2 Mobile apps must keep tokens and keys only in the secure storage of the operating system and never in preferences or in files.

# Section PIR-5: Incident Response

PIR-5.1 Alerts about repeated failed logins, privilege changes and access to card data must reach the on-call engineer within 15 minutes. PIR-5.2 Services must maintain appropriate procedures for responding to security incidents.

# Section PIR-6: Third-Party Components

PIR-6.1 Every third-party SDK or library must be approved before its first use, and the list of approved components must be reviewed every six months. PIR-6.2 Third-party scripts must not be loaded into web pages that handle card data or credentials.

# Section PIR-7: Recovery

PIR-7.1 Databases must have point-in-time recovery enabled with at least seven days of retention. PIR-7.2 The recovery time objective of a critical service must not exceed 4 hours, and it must be proven by a failover exercise at least once a year. PIR-7.3 For batch services a recovery time objective of up to 24 hours is acceptable.
