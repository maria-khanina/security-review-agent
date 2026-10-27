# Merchant Portal API - Introduction for New Developers

Welcome! This page explains how the merchant portal works, step by step.

## Step 1: What is it?

The merchant portal is a website where merchants look at their settlements, invite colleagues and ask for reports. The website calls an API. In front of the API sits the Portal Gateway. Behind it is the portal-backend service with its database portal-db (PostgreSQL). Login goes through Keycloak.

## Step 2: The endpoints

1. `GET /v1/settlements` - list the settlements of the merchant
2. `GET /v1/settlements/{settlementId}` - one settlement with its lines
3. `POST /v1/users` - invite a colleague
4. `PATCH /v1/users/{userId}/role` - change the role of a colleague
5. `POST /v1/reports` - ask for a transaction report
6. `GET /v1/reports/{reportId}` - download the report

## Step 3: Running it on your laptop

You need Docker. Start the compose file, it starts a database with fake merchants. ⟦F1|If you need to see a problem that only happens with real data, ask a colleague to copy the production records for that merchant to your laptop and delete them when you are done.⟧

## Step 4: The rules of the house

Please learn these, they apply to everything you build:

- ⟦S:ARC-01|Transaction records are kept for 7 years and deleted within 90 days after that.⟧
- ⟦S:ARC-02|Documents uploaded by customers are deleted within 30 days after the account is closed.⟧
- ⟦S:VUL-01|Critical vulnerabilities are fixed in production within 7 days after they are published.⟧
- ⟦S:VUL-02|Third-party components are never more than two major versions behind the latest release, and the register shows the version of each.⟧
- ⟦S:TST-02|Test accounts in production are removed within 7 days after the test ends.⟧
- ⟦S:NTF-01|Messages to customers never contain card numbers, passwords or images of identity documents.⟧
- ⟦S:EXP-01|Exported files with personal data are encrypted and deleted from the download location after 7 days.⟧
- ⟦S:EXP-02|Exports of more than 1,000 customer records need the written approval of the data owner.⟧
- ⟦S:INV-01|Every service has a named owner and a named deputy in the service register.⟧
- ⟦S:INV-02|The register lists the personal data of each service and every third party that receives data from it.⟧
- ⟦S:MON-01|Alerts of severity high are acknowledged within 15 minutes.⟧

## Step 5: Questions?

Ask in the channel of the team.
