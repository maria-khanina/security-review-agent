# Meridian Pay Information Security Policy

Document owner: Chief Information Security Officer. Version 4.2. Applies to all employees, contractors and systems that process Meridian Pay or customer data.

## 1. Purpose and Scope

1.1 This policy establishes the minimum security requirements for the design, development and operation of Meridian Pay services. 1.2 It applies to all production, staging and development systems, and to every third party that handles Meridian Pay data on our behalf. 1.3 Engineering teams are responsible for implementing these requirements, and the Security Architecture group reviews designs for compliance. 1.4 Exceptions require written approval from the CISO and expire after twelve months.

## 2. Identity and Access Management

2.1 Every externally reachable API endpoint must authenticate callers using OAuth2 or OpenID Connect bearer tokens, or mutual TLS. 2.2 Calls between internal services must be authenticated with mutual TLS or signed workload identity tokens, and network location alone is not sufficient proof of identity. 2.3 Access tokens must have a limited lifetime appropriate to the sensitivity of the operation and must be renewable only through a controlled refresh process. 2.4 Administrative and back-office access to production systems must require multi-factor authentication. 2.5 User passwords must be stored only as salted hashes produced with argon2id or bcrypt, and reversible storage of passwords is prohibited.

2.6 Every request that reads or changes a customer-owned resource must verify that the caller is entitled to that resource. 2.7 Employees shall be granted only the roles needed for their duties, and roles must be defined separately for each service. 2.8 Administrative and debug interfaces must not be reachable from the public internet. 2.9 Access rights to production systems must be reviewed at least quarterly by the system owner.

## 3. Cryptography

3.1 Personally identifiable information must be encrypted at rest using AES-256 or a stronger approved algorithm. 3.2 Primary account numbers must never be stored in clear text and must be tokenized through the card token vault. 3.3 All traffic crossing the boundary of Meridian Pay networks must be protected using TLS 1.2 or higher. 3.4 Sensitive communications between internal components shall be protected in transit. 3.5 Only cryptographic algorithms on the approved list may be used, and the use of MD5, SHA-1, DES, 3DES and ECB mode is prohibited. 3.6 Cryptographic keys must be managed securely throughout their lifecycle in accordance with industry practice.

## 4. Secrets Management

4.1 Secrets, including passwords, API keys and private keys, must not appear in source code, configuration files, API specifications or infrastructure definitions. 4.2 Runtime secrets should be retrieved from the approved secret store when a service starts.

## 5. Network Security

5.1 Databases and message brokers must not be publicly reachable and must be deployed in private subnets. 5.2 Object storage buckets must block public access and be private by default. 5.3 Management ports such as SSH and RDP, as well as database ports, must not be open to 0.0.0.0/0. 5.4 Appropriate perimeter controls shall be in place to protect externally exposed services from abusive traffic.

## 6. Logging and Monitoring

6.1 Authentication failures, privilege changes and access to sensitive data must be logged. 6.2 Logs should avoid recording sensitive data wherever practicable. 6.3 Audit logs must be tamper-evident and retained for at least one year. 6.4 Access to centralized logs must be restricted to authorized personnel. 6.5 Audit logs older than 90 days may be archived or deleted by the owning team.

## 7. Data Protection and Privacy

7.1 Services must collect and store only the personal data that is necessary for their stated purpose. 7.2 Personal data must be retained only for as long as is reasonably necessary and must be disposed of appropriately when it is no longer required. 7.3 Personal data may be disclosed to a third party only under an approved data processing agreement, and only the fields required for the purpose may be shared. 7.4 Reports and exports containing personal data must be accessible only to authorized users, must be encrypted in storage and must expire after a defined period.

## 8. Application Security

8.1 All external inputs must be validated against a defined schema and rejected if they do not conform. 8.2 Database queries must be parameterized, and constructing queries by concatenating user input is prohibited.

## 9. Operations

9.1 Continuous integration pipelines must scan dependencies and container images, and identified vulnerabilities must be remediated in a timely manner according to their severity. 9.2 Backups must be appropriately protected, and the ability to restore from backup must be verified at regular intervals.

## 10. Compliance and Review

10.1 This policy is reviewed annually and after any significant security incident. 10.2 Violations may result in disciplinary action in accordance with HR procedures.
