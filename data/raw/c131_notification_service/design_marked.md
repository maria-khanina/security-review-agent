# Notification Service - design (two parts, merged)

> Part A by Nadia (product engineering), Part B by Boris (platform). Merged in a hurry before the review; the two parts use different names for the same things (glossary at the end, not complete).

## Part A - What we build (Nadia)

The **Notification Service** sends e-mails, SMS and push messages to our customers when something happens: a payment arrived, a transfer failed, a card was blocked. Before this service every team sent its own messages with its own template, which gave us **five different looks for one e-mail** and no place to answer "did the customer get it?".

### Pieces

- **notifier** - the service that decides what to send and sends it. In my half I call it "the sender".
- **domain-events (Kafka)** - the stream on which the other services publish what happened. The notifier reads it.
- **Email and SMS provider** - the external company that delivers the messages. We pay per message.

### API

Four calls, all under /v1.

1. POST /v1/notifications sends a notification to a customer.
2. GET /v1/notifications/{notificationId} shows the delivery status.
3. PUT /v1/templates/{templateId} creates or replaces a template.
4. GET /v1/notifications lists notifications.

### How a message goes

1. A service publishes an event on domain-events, or calls the API directly for a message that is not tied to an event.
2. The notifier finds the template for the event, fills it in with the customer's details, and chooses the channel by the preference of the customer.
3. The message goes to the provider; the provider answers later with delivered, bounced or failed, and the notifier updates the status.

⟦F2|The notifier writes request logs for every call it receives and for every call it makes to the provider.⟧

Messages that fail are retried with growing delays up to twenty-four hours. Customers who unsubscribed from marketing messages are never sent marketing messages, but they still get messages about their own money.

---

## Part B - Platform and security (Boris)

Hi, I'm doing the infra half. In my part the notifier is "the service" and the provider is "the vendor" - sorry for the naming, Nadia uses other words.

**Webhooks.** The vendor reports delivery results by calling a webhook of ours. ⟦F1|The webhook sender of the service follows redirects and calls any host without an allow-list.⟧ The vendor can also be asked to call back a second address, which is configured by hand.

**Partner access.** Some partner systems call the API directly. ⟦F3|The API keys given to partners never expire.⟧ The keys are created by hand by the platform team and sent to the partner's contact.

**Controls.** The platform team's standard statements apply, and for this service they read like this:

* ⟦S:AUTH-02|Internal service calls are authenticated with mutual TLS or signed workload identity tokens.⟧
* ⟦S:AUTH-03|Access tokens expire within 15 minutes; refresh tokens are rotated on use.⟧
* ⟦S:CRYPTO-04|Traffic between services and to data stores is encrypted in transit.⟧
* ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧
* ⟦S:CRYPTO-06|Encryption keys are held in KMS, never stored with the data they protect, and rotated at least annually.⟧
* ⟦S:CRYPTO-07|Services validate TLS certificates and never disable verification.⟧
* ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧
* ⟦S:SECRET-02|Runtime secrets are fetched from the approved secret store at startup.⟧
* ⟦S:NET-01|The database and the message brokers sit in private subnets and are not publicly reachable.⟧
* ⟦S:LOG-01|Authentication failures, privilege changes and access to sensitive data are logged.⟧
* ⟦S:DATA-03|Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.⟧
* ⟦S:DATA-04|Non-production environments do not contain real personal or card data.⟧
* ⟦S:API-03|Callback payloads, outbound and inbound, are signed, and the signatures are verified.⟧
* ⟦S:API-05|Database queries are parameterized, and concatenating user input into queries is prohibited.⟧
* ⟦S:OPS-01|The CI pipeline scans dependencies and images, and critical vulnerabilities are fixed within 14 days.⟧
* ⟦S:OPS-02|Containers run as a non-root user, with a read-only root filesystem where possible.⟧

**Capacity.** The service handles around two hundred messages a second at the peak (salary day mornings) and the average is below twenty. Templates are cached in memory and refreshed when a template is replaced. Kafka consumers scale with the number of partitions of domain-events, which is twelve.

### Glossary (incomplete)

| Nadia says | Boris says |
|---|---|
| the sender | the notifier / the service |
| the provider | the vendor |
| domain events | the event bus |

Old design: "Notifier v1" in the previous wiki (page moved, link no longer works). The dashboards of v1 are still linked from the team page (also not valid).
