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

The notifier writes request logs for every call it receives and for every call it makes to the provider.

Messages that fail are retried with growing delays up to twenty-four hours. Customers who unsubscribed from marketing messages are never sent marketing messages, but they still get messages about their own money.

---

## Part B - Platform and security (Boris)

Hi, I'm doing the infra half. In my part the notifier is "the service" and the provider is "the vendor" - sorry for the naming, Nadia uses other words.

**Webhooks.** The vendor reports delivery results by calling a webhook of ours. The webhook sender of the service follows redirects and calls any host without an allow-list. The vendor can also be asked to call back a second address, which is configured by hand.

**Partner access.** Some partner systems call the API directly. The API keys given to partners never expire. The keys are created by hand by the platform team and sent to the partner's contact.

**Controls.** The platform team's standard statements apply, and for this service they read like this:

* Calls between our own services carry a signed workload identity token or use mutual TLS, and the receiving service checks it.
* Access token lifetime is capped at 15 minutes, and using a refresh token rotates it.
* There are no global super-roles: each service has its own roles and people get only the ones their work needs.
* Connections to the database and between internal services use TLS.
* Error responses do not expose stack traces, SQL or internal hostnames.
* Cryptography is limited to the approved algorithm list, and the legacy ones (MD5, SHA-1, DES, 3DES, ECB) are banned.
* Encryption keys live in KMS, apart from the data they protect, and are rotated at least once a year.
* Reading centralized logs requires authorization, and only approved staff have it.
* Outbound TLS connections always verify the peer certificate.
* No secrets are kept in source code, config files, API specs or infrastructure definitions.
* On boot, the service pulls its credentials from the approved secret store.
* Each request for a customer's resource checks that the caller owns it or is entitled to it.
* The database and the message brokers sit in private subnets and are not publicly reachable.
* Security-relevant events (authentication failures, privilege changes, access to sensitive data) are logged.
* Third parties receive only the fields they need, and only if an approved data processing agreement covers them.
* Non-production environments contain no real personal or card data.
* Each export file is encrypted at rest, readable only by the authorized requester, and removed automatically after 72 hours.
* Inbound and outbound webhooks include an HMAC signature and a timestamp; verification of both is mandatory on the receiving side.
* We use parameterized queries only, with no SQL built from user input by string concatenation.
* External inputs are accepted only if they validate against the schema.
* Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less.
* Containers run as a non-root user, with a read-only root filesystem where possible.
* Audit logs are written to tamper-evident storage with at least one year of retention.
* The service stores only the personal fields that appear in its data inventory with a stated purpose.

**Capacity.** The service handles around two hundred messages a second at the peak (salary day mornings) and the average is below twenty. Templates are cached in memory and refreshed when a template is replaced. Kafka consumers scale with the number of partitions of domain-events, which is twelve.

### Glossary (incomplete)

| Nadia says | Boris says |
|---|---|
| the sender | the notifier / the service |
| the provider | the vendor |
| domain events | the event bus |

Old design: "Notifier v1" in the previous wiki (page moved, link no longer works). The dashboards of v1 are still linked from the team page (also not valid).
