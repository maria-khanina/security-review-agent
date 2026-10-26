#pgw-design  (pasted from slack, trimmed a bit, sorry)

**[10:12] dana:** ok so for the pgw review next week, can we agree what goes in the doc? i'll paste the thread

**[10:14] marcus:** the flow is merchant backend -> edge gw -> core -> db, then core calls the acquirer connector and drops events on payment-events. five boxes, that's it :+1:

**[10:15] marcus:** api = POST /v1/payments (amount, currency, card_token, merchant_id, reference), GET /v1/payments/{paymentId}, POST .../capture (amount), POST .../refunds (amount, reason), GET /v1/payments for the list. answers have id, status, amount, currency, last4, merchant_id (refund is just id/status/amount)

**[10:19] dana:** security stuff, i'll just write what we said in the meeting:

**[10:19] dana:** ⟦S:AUTH-01|No external endpoint serves anonymous traffic; callers present an OAuth2 token or a TLS client certificate.⟧ and ⟦S:AUTHZ-01|every request for a merchant-owned payment verifies that the caller owns it or is entitled to it.⟧

**[10:19] dana:** ⟦S:OPS-01|Vulnerability scanning of dependencies and images is part of CI, with critical issues fixed within two weeks.⟧

**[10:19] dana:** ⟦S:SECRET-02|On boot, the service pulls its credentials from the approved secret store.⟧

**[10:21] priya:** also ⟦S:AUTHZ-04|administrative and debug endpoints are not reachable from the public internet.⟧ (the old debug page was, we fixed it) and ⟦F2|access reviews are done only when somebody leaves the company.⟧ lena owns the review i think? TBD

**[10:21] priya:** ⟦S:AUTH-03|Access token lifetime is capped at 15 minutes, and using a refresh token rotates it.⟧

**[10:21] priya:** ⟦S:OPS-03|Encrypted backups are checked by a restoration exercise at least twice a year.⟧

**[10:24] marcus:** data: ⟦S:CRYPTO-01|personally identifiable information is encrypted at rest with AES-256⟧ , ⟦S:CRYPTO-02|primary account numbers are never stored in clear text and are tokenized by the card token vault⟧ , ⟦S:CRYPTO-03|all external traffic uses TLS 1.2 or higher⟧ and ⟦S:CRYPTO-05|only approved cryptographic algorithms are used, MD5, SHA-1, DES, 3DES and ECB mode are prohibited⟧

**[10:24] marcus:** ⟦S:DATA-02|Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.⟧

**[10:24] marcus:** ⟦S:LOG-03|The audit trail is tamper-evident, and we keep it for no less than twelve months.⟧

**[10:26] dana:** :thumbsup: and for personal data ⟦F1|free-text fields from the payment forms are saved verbatim, and they often contain extra personal data⟧ , , ⟦S:DATA-03|personal data is sent to third parties only under an approved data processing agreement and only the fields required⟧

**[10:26] dana:** ⟦S:CRYPTO-04|Nothing travels unencrypted inside our network, because service-to-service and service-to-datastore links are encrypted.⟧

**[10:27] priya:** and exports, ⟦S:DATA-05|reports and exports that contain personal data require authorization to access, are encrypted in storage and expire⟧ (finance csv thing)

**[10:27] priya:** ⟦S:LOG-04|Only authorized staff can access the central logs.⟧

**[10:27] priya:** ⟦S:LOG-02|Logs carry opaque identifiers only and never include secrets, card numbers or personal data.⟧

**[10:31] marcus:** secrets: ⟦S:SECRET-01|secrets do not appear in source code, configuration files, specifications or infrastructure definitions⟧ and

**[10:32] marcus:** network: ⟦S:NET-01|the database and the message brokers sit in private subnets and are not publicly reachable⟧

**[10:35] dana:** logging -> ⟦S:LOG-01|authentication failures, privilege changes and access to sensitive data are logged⟧ , ,

**[10:35] dana:** ⟦S:AUTH-02|We do not trust the internal network by itself: every internal call is authenticated with mTLS or workload identity tokens.⟧

**[10:38] priya:** code + ops: ⟦S:API-01|all external inputs are validated against a schema and rejected if invalid⟧ , ⟦S:API-05|database queries are parameterized and concatenating user input into queries is prohibited⟧ , ,

**[10:38] priya:** ⟦S:NET-05|Requests from the internet reach the API only through the WAF, where rate limits are enforced.⟧

**[10:38] priya:** ⟦S:CRYPTO-06|Encryption keys must be held in KMS, never stored with the data they protect, and rotated at least annually.⟧

**[10:41] dana:** perfect. who writes the "behavior" section?

**[10:42] marcus:** me. payments go created -> authorized -> captured -> refunded (partial ok), decline = failed. reference + merchant_id = idempotent create. partial capture allowed once, never above the authorized amount. every state change = event on payment-events, at-least-once so consumers dedupe on payment id

**[10:44] dana:** acquirer timeout? 10s or 15s?

**[10:44] marcus:** TBD :sweat_smile: contract says 15, i said 10 in the call

**[10:45] priya:** TBD. also TBD on whether the connector gets its own deployment

**[10:46] dana:** ok TBD TBD TBD. i'll write it up
