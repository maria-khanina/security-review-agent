Merchant Portal API - Design (copied from the v2 doc and the wiki)

Overview
The merchant portal is the back office for merchants. They look at settlements, manage their own users and request transaction reports. The web app talks to the Portal Gateway, the gateway authenticates with Keycloak and forwards to portal-backend. portal-backend reads portal-db (PostgreSQL).

Endpoints
GET /v1/settlements - list of settlements
GET /v1/settlements/{settlementId} - one settlement
POST /v1/users - invite a merchant user
PATCH /v1/users/{userId}/role - change role of a merchant user
POST /v1/reports - request a transaction report
GET /v1/reports/{reportId} - download

Reports
Reports are created in the background and are ready in a few minutes. ⟦S:EXP-01|Reports with personal data are encrypted and deleted from the download location after 7 days.⟧

Documents
(copied from wiki) ⟦F1|Documents that merchants upload are deleted after 12 months, so that support can answer late questions.⟧

Payments
(copied from wiki) ⟦F2|Large payments that stay in the hold queue for more than 24 hours are released automatically if nobody has reviewed them.⟧

Operating
(from the ops page)
- ⟦S:ARC-01|Transaction records are kept for 7 years and deleted within 90 days after that period.⟧
- ⟦S:VUL-01|Critical vulnerabilities are fixed in production within 7 days after they are published.⟧
- ⟦S:TST-01|Production data is not copied to test or development environments.⟧
- ⟦S:TST-02|Test accounts in production are removed within 7 days after the test ends.⟧
- ⟦S:NTF-01|Messages to merchants contain no card numbers, passwords or images of identity documents.⟧
- ⟦S:INV-02|The register lists the personal data of the portal and the third parties that receive data from it.⟧
- ⟦S:WHK-01|Callbacks to merchant endpoints are signed and carry a timestamp the receiver can check against replay.⟧

Register
⟦F3|The service register is a spreadsheet that the team has not opened since the launch, nobody remembers who is entered as the owner.⟧
