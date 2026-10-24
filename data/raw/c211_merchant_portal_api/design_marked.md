# Merchant Portal API: Design Document

## 1. Introduction

This document explains the design of the Merchant Portal API. It is written also for new team members, so some basic things are explained. A merchant is a shop or a business that accepts payments with Meridian Pay. The portal is the place where a merchant can look at the settlements (the money that Meridian Pay pays out), manage the people who can use the account of the merchant and download reports about the transactions.

## 2. Basic concepts

A **tenant** is one merchant and all its data. In a multi-tenant system many merchants use the same software and the same database, but each merchant must only see its own data. An **API** is a way for programs to talk with each other. The **Merchant web app** is the program that merchants use in the browser, and it talks to the Portal Gateway, which is the front door of the API.

## 3. Components

- **Portal Gateway** receives the calls of the Merchant web app and passes them to portal-backend, after it has asked Keycloak if the token of the user is valid.
- **portal-backend** is the service with the business logic.
- **portal-db** is the PostgreSQL database with the settlements and the merchant users.
- **Keycloak** is the identity provider that holds the user accounts.

## 4. Endpoints

**GET /v1/settlements** lists the settlements of the merchant. Each item has id, period, gross, fees and net. Gross is the sum of all payments, fees is what Meridian Pay takes and net is gross minus fees.

**GET /v1/settlements/{settlementId}** returns one settlement with the same fields.

**POST /v1/users** invites a new user of the merchant. The request has email and role, and the response has id, email and role. A role is a set of things that the user is allowed to do, for example `viewer` or `admin`.

**PATCH /v1/users/{userId}/role** changes the role of a user. The response has id, email and role.

**POST /v1/reports** asks for a transaction report with report_type, from_date and to_date. The response has id, status and expires_at. Reports are created in the background, so the status is first `pending`, and then `ready`.

**GET /v1/reports/{reportId}/download** downloads a finished report and returns id, status and expires_at in the headers.

## 5. Data of the merchants

Because the portal is multi-tenant, the data of every merchant needs to be kept apart. ⟦S:TEN-01|Every query on merchant data is filtered by the tenant identifier taken from the authenticated token and never from a request parameter.⟧ ⟦S:TEN-02|The tenant data in portal-db is separated by row-level security, so one tenant cannot read the rows of another tenant.⟧

## 6. Files that merchants upload

Merchants can upload a company logo and a CSV file with the users that they want to invite. ⟦F2|The upload endpoint stores the file as it is and accepts any content type, because the files are only stored and shown back to the merchant.⟧ ⟦S:UPL-02|Uploaded files are scanned for malware before any other user or service can open them.⟧

## 7. The web app

The Merchant web app shows the settlements, the users and the reports. ⟦F1|To answer the questions of merchants quickly, the chat widget of a support vendor is embedded in all pages of the portal, including the login page where the merchants enter their password.⟧

## 8. Operation and recovery

⟦S:IR-01|Alerts about repeated failed logins, privilege changes and access to card data reach the on-call engineer within 15 minutes.⟧ ⟦S:TPC-01|Every third-party SDK or library is approved before its first use, and the list of approved components is reviewed every six months.⟧ ⟦S:DR-01|portal-db has point-in-time recovery switched on with a retention of seven days.⟧

## 9. Failure handling

If the report job fails, the report gets the status `failed` and the merchant can ask for it again. A report that is ready can be downloaded until expires_at, which is seven days after the creation, and after that it is deleted.

## 10. Rollout

The portal API is released together with a new version of the Merchant web app. First, ten merchants of the pilot group use it for two weeks. After that, all merchants move.

## 11. Open questions

- Should the role `viewer` be allowed to download reports?
- The CSV file for inviting users has at most 500 rows; is this enough for big merchants?
