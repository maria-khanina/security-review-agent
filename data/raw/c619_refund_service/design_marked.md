REFUND SERVICE - tickets collected into a doc

RF-101 request a refund
POST /v1/refunds with payment id, amount, reason. Creates a refund in `requested`.

RF-102 approve or reject
POST /v1/refunds/{refundId}/approval. Needs a second person for refunds above the merchant limit.

RF-103 cancel
POST /v1/refunds/{refundId}/cancellation, only while `requested`.

RF-104 read
GET /v1/refunds/{refundId}, GET /v1/refunds

RF-110 events
refund-events (Kafka) gets `requested`, `approved`, `rejected`, `cancelled`, `paid`.

RF-120 where it runs
Refunds Gateway (entrance) -> refund-core -> refund-db (PostgreSQL). ⟦F3|The refund-core stores every refund and its history in refund-db.⟧

RF-130 register
⟦F2|The register lists three people as owners of the refund service: Ola, Piet and Sanne.⟧ ⟦S:INV-02|The register lists the personal data of the refund service and each third party that receives data from it.⟧

RF-131 versions
⟦F1|The versions of the components are in the build files only; no other place records them.⟧

RF-140 other
- ⟦S:ARC-02|Documents uploaded by customers are deleted within 30 days after the account is closed.⟧
- ⟦S:VUL-01|Critical vulnerabilities are fixed in production within 7 days after publication.⟧
- ⟦S:TST-01|No production data in test or development environments.⟧
- ⟦S:TST-02|Test accounts in production removed within 7 days after the test ends.⟧
- ⟦S:FRD-01|Transactions above 10,000 EUR are held for review by the fraud team before they are settled.⟧
- ⟦S:MON-01|High alerts are acknowledged within 15 minutes.⟧
