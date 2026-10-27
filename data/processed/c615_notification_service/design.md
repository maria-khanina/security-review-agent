notifier design (security champion edition, so there will be a lot of rules)

what: consumes domain events from Kafka, builds email/SMS/push from templates, sends via the provider.

api:
POST /v1/notifications, GET /v1/notifications/{id}, PUT /v1/templates/{id}, GET /v1/notifications

flow: event -> template -> fill -> provider -> delivery status callback stored

verification mails: the verification email for a new customer attaches the image of the identity document that was uploaded, so that the customer can see what we received.

what we do right:
* Critical vulnerabilities are fixed in production within 7 days after they are published.
* No production data is copied to test or development environments.
* Test accounts in production are removed within 7 days after the test ends.
* The service register names an owner and a deputy of the notifier.
* The register lists the personal data of the notifier and each third party that receives data, the provider.
* Transactions above 10,000 EUR are held for review by the fraud team before they are settled.
* High alerts are acknowledged within 15 minutes.
* Delivery callbacks to customer endpoints are signed and carry a timestamp that the receiver can check against replay.

customer data: When a customer closes the account, the documents are deleted when the customer asks for it; nothing is deleted automatically. Notification records are deleted from the main database after the retention period, but they stay in the nightly exports.

todo: digest mails
