# Meridian Pay Operations and Data Lifecycle Standard

This standard sets the controls for the life of records and documents, the handling of vulnerabilities, test environments, messages and exports, the register of services, the review of large payments and the response to alerts. Each requirement is numbered so that audit findings can cite it. Where a requirement says "must", deviation needs an approved exception.

# Section OLS-1: Records and Documents

OLS-1.1 Transaction records must be kept for 7 years and must be deleted within 90 days after that period ends. OLS-1.2 Documents uploaded by customers must be deleted within 30 days after the account is closed. OLS-1.3 Documents that are needed for a pending dispute may be kept until the dispute is settled.

# Section OLS-2: Vulnerabilities and Components

OLS-2.1 Vulnerabilities rated critical must be fixed in production within 7 days after they are published. OLS-2.2 Third-party components should be kept reasonably up to date.

# Section OLS-3: Test Environments

OLS-3.1 Production data must not be copied to test or development environments. OLS-3.2 Test accounts in production should be removed within 7 days after the test ends.

# Section OLS-4: Messages and Exports

OLS-4.1 Messages sent to customers must not contain card numbers, passwords or images of identity documents. OLS-4.2 Exported files that contain personal data must be encrypted and must be deleted from the download location after 7 days. OLS-4.3 Large exports of customer records require appropriate approval.

# Section OLS-5: Register of Services

OLS-5.1 Every service must have a named owner and a named deputy in the service register. OLS-5.2 The service register must list for each service the personal data that it processes and every third party that receives data from it.

# Section OLS-6: Payments and Alerts

OLS-6.1 Transactions above 10,000 EUR must be held for review by the fraud team before they are settled. OLS-6.2 Alerts of severity high must be acknowledged within 15 minutes. OLS-6.3 Outside office hours alerts of severity high may be acknowledged within two hours. OLS-6.4 Callbacks to endpoints of customers must be signed and must carry a timestamp that the receiver can check against replay.
