#pgw-design  (pasted from slack, trimmed a bit, sorry)

**[10:12] dana:** ok so for the pgw review next week, can we agree what goes in the doc? i'll paste the thread

**[10:14] marcus:** the flow is merchant backend -> edge gw -> core -> db, then core calls the acquirer connector and drops events on payment-events. five boxes, that's it :+1:

**[10:15] marcus:** api = POST /v1/payments (amount, currency, card_token, merchant_id, reference), GET /v1/payments/{paymentId}, POST .../capture (amount), POST .../refunds (amount, reason), GET /v1/payments for the list. answers have id, status, amount, currency, last4, merchant_id (refund is just id/status/amount)

**[10:19] dana:** security stuff, i'll just write what we said in the meeting:

**[10:19] dana:** ⟦S:AUTH-01|Every externally reachable API endpoint authenticates callers with OAuth2/OIDC bearer tokens or mutual TLS.⟧ and ⟦S:AUTHZ-01|every request for a merchant-owned payment verifies that the caller owns it or is entitled to it.⟧

**[10:21] priya:** also ⟦S:AUTHZ-04|administrative and debug endpoints are not reachable from the public internet.⟧ (the old debug page was, we fixed it) and ⟦S:AUTHZ-05|access rights to production systems are reviewed at least quarterly.⟧ lena owns the review i think? TBD

**[10:24] marcus:** data: ⟦S:CRYPTO-01|personally identifiable information is encrypted at rest with AES-256⟧ , ⟦S:CRYPTO-02|primary account numbers are never stored in clear text and are tokenized by the card token vault⟧ , ⟦S:CRYPTO-03|all external traffic uses TLS 1.2 or higher⟧ and ⟦S:CRYPTO-05|only approved cryptographic algorithms are used, MD5, SHA-1, DES, 3DES and ECB mode are prohibited⟧

**[10:26] dana:** :thumbsup: and for personal data ⟦S:DATA-01|we collect and store only the personal data needed for payment processing⟧ , , ⟦S:DATA-03|personal data is sent to third parties only under an approved data processing agreement and only the fields required⟧

**[10:27] priya:** and exports, ⟦S:DATA-05|reports and exports that contain personal data require authorization to access, are encrypted in storage and expire⟧ (finance csv thing)

**[10:31] marcus:** secrets: ⟦S:SECRET-01|secrets do not appear in source code, configuration files, specifications or infrastructure definitions⟧ and

**[10:32] marcus:** network: ⟦S:NET-01|the database and the message brokers sit in private subnets and are not publicly reachable⟧

**[10:35] dana:** logging -> ⟦S:LOG-01|authentication failures, privilege changes and access to sensitive data are logged⟧ , ,

**[10:38] priya:** code + ops: ⟦S:API-01|all external inputs are validated against a schema and rejected if invalid⟧ , ⟦S:API-05|database queries are parameterized and concatenating user input into queries is prohibited⟧ , ,

**[10:41] dana:** perfect. who writes the "behavior" section?

**[10:42] marcus:** me. payments go created -> authorized -> captured -> refunded (partial ok), decline = failed. reference + merchant_id = idempotent create. partial capture allowed once, never above the authorized amount. every state change = event on payment-events, at-least-once so consumers dedupe on payment id

**[10:44] dana:** acquirer timeout? 10s or 15s?

**[10:44] marcus:** TBD :sweat_smile: contract says 15, i said 10 in the call

**[10:45] priya:** TBD. also TBD on whether the connector gets its own deployment

**[10:46] dana:** ok TBD TBD TBD. i'll write it up
