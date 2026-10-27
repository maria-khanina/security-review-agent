# Wallet Service - Design Statement

## 1. Introduction

This document sets out the design of the wallet service and the commitments that apply to it.

## 2. Design

The wallet service keeps the balance of each customer wallet. Customers use a mobile application, which reaches the service through the Mobile API Gateway. The gateway validates tokens with Keycloak and forwards authenticated requests to wallet-core. The wallet-core service stores balances and transactions in wallet-db (PostgreSQL).

The interface offers: retrieval of a wallet and its balance, top-up from a funding source, transfer between wallets, listing of transactions and update of the wallet profile.

## 3. Commitments

3.1 Records. ⟦S:ARC-01|Transaction records are kept for 7 years and are deleted within 90 days after that period ends.⟧ ⟦S:ARC-02|Documents uploaded by customers are deleted within 30 days after the account is closed.⟧

3.2 Vulnerabilities and components. ⟦F2|The deadline for fixing vulnerabilities rated critical is 30 days, because the release train runs monthly.⟧ ⟦S:VUL-02|Third-party components are not more than two major versions behind the latest release, and the service register shows the version of each.⟧

3.3 Test environments. ⟦S:TST-01|Production data is not copied to test or development environments.⟧

3.4 Messages. ⟦S:NTF-01|Messages to customers do not contain card numbers, passwords or images of identity documents.⟧

3.5 Register. ⟦S:INV-02|The register lists the personal data that the wallet service processes and each third party that receives data from it.⟧

3.6 Payments. ⟦F1|Transactions of trusted merchants are never held for review, whatever the amount; transactions of other merchants above 10,000 EUR are held for the fraud team.⟧

3.7 Operations. ⟦S:MON-01|Alerts of severity high are acknowledged within 15 minutes.⟧
