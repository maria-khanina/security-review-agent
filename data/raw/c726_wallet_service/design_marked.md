Wallet service design (ESL)

The wallet keep the balance of the customer. The customer can top up, send money to other wallet, look at transactions and change the profile. The mobile app talk to Mobile API Gateway, the gateway ask Keycloak and send to wallet-core. The wallet-core use wallet-db (PostgreSQL).

API: GET /v1/wallets/{walletId}, POST /v1/wallets/{walletId}/topups, POST /v1/transfers, GET /v1/wallets/{walletId}/transactions, PATCH /v1/wallets/{walletId}/profile.

What we do:
2. ⟦S:REC-02|Differences found in a reconciliation are resolved within 5 working days.⟧
3. ⟦S:IDM-01|Every operation that move money take an idempotency key, and a repeated request with the same key does not move the money again.⟧
5. ⟦F1|When we remove an old API version, the removal is announced on the mailing list, that most customers have left.⟧
6. ⟦S:VER-02|Breaking changes of the API are released only as a new version of the API.⟧
7. ⟦S:SBX-01|The merchant sandbox contain only generated data and run separately from production.⟧
8. ⟦F2|Failed messages are retried forever, so one bad message can block a queue.⟧
9. ⟦S:MSG-02|Messages are deleted from the queue after they are processed.⟧
11. ⟦S:SUP-01|Support agents see card numbers and document numbers only in masked form.⟧
12. ⟦S:SUP-02|A change of the phone number or the email address need a one-time code that is sent to the old contact data.⟧
