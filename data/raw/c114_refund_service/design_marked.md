# Refund Service - a simple explanation of the design

Written by Lukas (junior backend engineer). Reviewer: Ana.

## 1. What is a refund and who asks for it?

A customer pays a merchant with a card and later wants the money back, for example because the goods were broken. The merchant (or one of our support agents, when the merchant cannot be reached) asks us to send the money back to the card. This is called a refund. The Refund Service is the part of the platform that receives such a request, checks it, remembers it and tells the other services what happened to it. I learned that a refund is not always the whole payment: it can be a part of it, and a payment can have more than one refund until the sum reaches the amount paid.

## 2. The four parts

1. **Refunds Gateway.** The door of the service. All requests from the merchants and from the support console come to this door first and it hands them to the core.
2. **refund-core.** The service with the logic: it keeps the rules of what can be refunded, the states of a refund and the approval.
3. **refund-db (PostgreSQL).** The database with the refund records. A record has the id of the payment, the amount, the currency, the reason and the state. I call it the "memory" of the service.
4. **refund-events (Kafka).** A line of messages, so the other services (the ledger, the notification service) hear about every change. I wrote "line" because a queue is the same thing in simple words; the team says topic.

How it moves: merchant backend or support agent -> Refunds Gateway -> refund-core -> refund-db, and refund-core also puts a message to refund-events.

## 3. The API

There are five calls, all start with /v1.

- **POST /v1/refunds** asks for a refund. The body has payment_id, amount, currency, reason and requested_by. The answer is the refund with id, payment_id, status, amount and currency.
- **GET /v1/refunds/{refundId}** shows one refund.
- **GET /v1/refunds** shows a list and can be filtered by status and payment_id.
- **POST /v1/refunds/{refundId}/approval** approves or rejects a refund. The body has decision and comment.
- **POST /v1/refunds/{refundId}/cancellation** cancels a refund that is still pending. The body has a reason.

## 4. The life of a refund

A refund starts as pending. Small refunds are approved automatically. Bigger refunds wait until a second person writes the approval; the person who asked cannot approve his own request. After the approval the money is sent back and the refund becomes completed. If something goes wrong with the card network the refund becomes failed and a person looks at it. A pending refund can be cancelled, a completed one cannot. Every change puts a message to refund-events.

⟦F2|Every request comes through Refunds Gateway, which passes it to refund-core together with the identity of the caller.⟧

## 5. Security - what I understood

My reviewer asked me to explain the security part in simple words, so I wrote what I found in the standards.

**Who is the caller?** ⟦S:AUTH-01|No external endpoint serves anonymous traffic; callers present an OAuth2 token or a TLS client certificate.⟧ ⟦F1|The lifetime of an access token is configurable for each client, and most merchants set it to thirty days so that their systems do not need to sign in again.⟧ ⟦S:AUTH-06|Failed attempts on the login and token endpoints are throttled, and the account is temporarily locked after ten consecutive failures.⟧

⟦S:LOG-03|Audit logs must be tamper-evident and retained for at least one year.⟧
⟦S:SECRET-03|Credentials rotate on a 90-day cycle at the latest, and at once after a suspected leak.⟧

⟦S:CRYPTO-03|External traffic is served over TLS 1.2 or newer.⟧
⟦S:OPS-03|Backups are encrypted, and restores are tested at least twice a year.⟧

**Where are the doors?** ⟦S:AUTHZ-04|The admin interface and the debug endpoints sit behind the internal network boundary and have no public route.⟧ ⟦S:NET-05|A WAF with rate limiting protects the externally exposed API.⟧ ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧ ⟦S:NET-04|Services that call third parties have their egress restricted to an approved allowlist.⟧

**Card data.** Card numbers are the most dangerous thing we have. ⟦S:CRYPTO-02|Primary account numbers are never stored in clear text and are tokenized by the card token vault.⟧ ⟦S:CRYPTO-01|Databases and buckets that hold personal data use AES-256 encryption at rest, and the keys are managed in the corporate key management service.⟧ ⟦S:CRYPTO-05|Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.⟧ ⟦S:CRYPTO-06|Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year.⟧ ⟦S:CRYPTO-07|TLS certificate verification is enabled in all clients, with no option to disable it.⟧

⟦S:LOG-04|Access to the centralized logging system is restricted to authorized people.⟧

⟦S:CRYPTO-04|Nothing travels unencrypted inside our network, because service-to-service and service-to-datastore links are encrypted.⟧

**Secrets.** A secret is a password or a key. ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ ⟦S:SECRET-02|At startup the service fetches its secrets from the approved secret store.⟧

**Logs and test data.** ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧ ⟦S:DATA-04|Only synthetic data is present outside production.⟧ ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧

⟦S:DATA-05|Reports and exports with personal data are available only to authorized users, stored encrypted, and deleted after 7 days.⟧

**Input, errors and code.** ⟦S:API-01|Schema validation runs on every external input, and invalid data never reaches the business logic.⟧ ⟦S:API-03|Webhook payloads are HMAC-signed and timestamped, and the receiver verifies the signature and the timestamp before accepting them.⟧ ⟦S:API-05|All queries use bound parameters instead of string concatenation.⟧ ⟦F3|Error responses include the stack trace and the SQL text in all environments, because it makes the search for mistakes faster.⟧ ⟦S:OPS-01|Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less.⟧ ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧

⟦S:DATA-01|The service stores only the personal fields that appear in its data inventory with a stated purpose.⟧

## 6. What the dashboards show

One dashboard per environment shows the number of refunds in an hour, the share of refunds in the states failed and pending, and the age of the oldest pending refund. An alert starts when a refund is pending for longer than the limit in the runbook. The support team also gets a list of all refunds that are older than three days and not completed.

## 7. Questions for the review

- Is automatic approval of small refunds a good idea or should every refund be approved by a person?
- How long do we keep the refund records after the refund is completed?
- Should the support console see refunds of all merchants or only of the merchants of one support team? (see the old ticket REF-14, link not valid)
