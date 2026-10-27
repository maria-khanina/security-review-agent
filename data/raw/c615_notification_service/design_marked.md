notifier design (security champion edition, so there will be a lot of rules)

what: consumes domain events from Kafka, builds email/SMS/push from templates, sends via the provider.

api:
POST /v1/notifications, GET /v1/notifications/{id}, PUT /v1/templates/{id}, GET /v1/notifications

flow: event -> template -> fill -> provider -> delivery status callback stored

verification mails: ⟦F1|the verification email for a new customer attaches the image of the identity document that was uploaded, so that the customer can see what we received.⟧

what we do right:
* ⟦S:VUL-01|Critical vulnerabilities are fixed in production within 7 days after they are published.⟧
* ⟦S:TST-01|No production data is copied to test or development environments.⟧
* ⟦S:TST-02|Test accounts in production are removed within 7 days after the test ends.⟧
* ⟦S:INV-01|The service register names an owner and a deputy of the notifier.⟧
* ⟦S:INV-02|The register lists the personal data of the notifier and each third party that receives data, the provider.⟧
* ⟦S:FRD-01|Transactions above 10,000 EUR are held for review by the fraud team before they are settled.⟧
* ⟦S:MON-01|High alerts are acknowledged within 15 minutes.⟧
* ⟦S:WHK-01|Delivery callbacks to customer endpoints are signed and carry a timestamp that the receiver can check against replay.⟧

customer data: ⟦F2|When a customer closes the account, the documents are deleted when the customer asks for it; nothing is deleted automatically.⟧ ⟦F3|Notification records are deleted from the main database after the retention period, but they stay in the nightly exports.⟧

todo: digest mails
