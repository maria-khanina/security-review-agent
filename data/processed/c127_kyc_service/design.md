# kyc service

ok so the kyc service, i'll try to explain it in the order things happen to a customer because thats the only way it makes sense to me. a new customer in the app has to prove who they are before they can do anything above the small limits, so the app opens a case with the kyc-orchestrator (the thing everyone calls "the orchestrator" or just kyc, same service), then uploads photos of the identity document one by one, the orchestrator stores the images in the kyc-documents bucket (S3) and the case data in kyc-db (PostgreSQL), and when the customer is happy they submit the case, which sends the case to the Identity verification vendor, the vendor answers some minutes later (or hours, i've seen hours) and the case moves to verified or rejected, and the app polls the status. there is also a list call for the support people to see cases (TBD whether support gets its own endpoint, now they use the same list). the five calls are POST /v1/kyc/cases to open, POST /v1/kyc/cases/{caseId}/documents to upload, GET /v1/kyc/cases/{caseId} for status, POST /v1/kyc/cases/{caseId}/submit to send to the vendor and GET /v1/kyc/cases to list.

When something goes wrong, the kyc-orchestrator answers the app with an HTTP status code and the app shows its own generic message. i dont remember if there is a body, check with the app team (TBD).

what gets stored, honestly i have to say Every field received from the client is saved, in case analytics needs it later. nobody asked for this, it just happened in the first version and then we left it, and The developers share one database login, which is also used by the production service. it was easier for the first release and we keep saying we will change it (TBD, no owner).

now the list from the platform checklist, i'll paste the ones that apply and say it simply. No external endpoint serves anonymous traffic; callers present an OAuth2 token or a TLS client certificate. Access tokens live for at most 15 minutes, and every refresh token is replaced when it is used. Repeated failed logins are slowed down, and ten consecutive failures trigger a temporary lockout of the account. Every request for a merchant-owned resource verifies that the caller owns the resource or is entitled to it. (for kyc it is customer-owned of course, the check is the same idea) Administrative and debug endpoints are not reachable from the public internet. then crypto, Personal data in our databases and object storage is encrypted at rest with AES-256, using keys held in the corporate key management service. We use only approved cryptographic algorithms and never MD5, SHA-1, DES, 3DES or ECB mode. KMS holds the keys, the data stores only keep ciphertext, and key rotation happens at least yearly. Hostname verification is disabled on the connection to the acquirer. then secrets Secrets do not appear in source code, configuration files, specifications or infrastructure definitions. Runtime secrets are read from the secret store when the service starts. and network The database and the message brokers sit in private subnets and are not publicly reachable. The kyc-documents bucket blocks public access and is private by default. Outbound firewall rules are managed by each team and are rarely reviewed. then We log failed logins, changes of privileges and reads of sensitive data. Data goes to the processor under the signed data processing agreement and only the fields it needs for the contracted task are sent: the order reference and the delivery address, because nothing else is required for delivery. Only synthetic data is present outside production. and last the code ones All external input is validated against a schema, and invalid requests are rejected. Every webhook we send or receive is signed with an HMAC, and the receiver checks the signature together with the timestamp. Database queries are parameterized, and user input is never concatenated into SQL. Every build scans libraries and container images, and critical vulnerabilities get a 14-day fix deadline. Workloads are non-root, and read-only root filesystems are used wherever they can be.

Service credentials must be rotated at least every 90 days and immediately after suspected exposure.

The audit trail is tamper-evident, and we keep it for no less than twelve months.

Rate limit per client: 60 requests per minute, with HTTP 429 and a Retry-After header once the limit is hit.

Exports containing personal data expire after 14 days, are encrypted in storage and can be downloaded only by authorized users.

Access to the central logs is limited to the on-call engineers of the owning team, who need it to investigate incidents, and to the security analysts, who need it to review audit events.

Logs carry opaque identifiers only and never include secrets, card numbers or personal data.

Requests from the internet reach the API only through the WAF, where rate limits are enforced.

Traffic between services, and from services to data stores, is encrypted in transit.
Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.

We do not trust the internal network by itself: every internal call is authenticated with mTLS or workload identity tokens.

other things, the vendor has a daily limit of cases which we hit twice last month, so submit can return an error and the case stays in the submitted-waiting state (TBD, retry policy not written down), document images are limited to ten megabytes each, and the retention of rejected cases is not decided yet (TBD, legal), i keep meaning to write all this properly.
