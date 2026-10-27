# Notification Service

## Overview

| Item | Value |
|---|---|
| Service | notifier |
| Input | domain-events (Kafka) and direct API calls |
| Output | email, SMS and push messages via the Email and SMS provider |

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | /v1/notifications | send a notification |
| GET | /v1/notifications/{notificationId} | delivery status |
| PUT | /v1/templates/{templateId} | create or replace a template |
| GET | /v1/notifications | list notifications |

## Behavior

The notifier consumes domain events (payment captured, refund approved, account closed, password reset requested), picks the template of the event type, fills it and hands the message to the provider. Delivery status comes back by a callback and is stored. A message that the provider rejects is retried three times, 1 minute apart, and then marked `failed`.

## Obligations

| Topic | Commitment |
|---|---|
| Messages | ⟦S:NTF-01|Messages to customers never contain card numbers, passwords or images of identity documents.⟧ |
| Documents | ⟦S:ARC-02|Documents uploaded by customers are deleted within 30 days after the account is closed.⟧ |
| Components | ⟦S:VUL-02|Third-party components are not more than two major versions behind the latest release; the register shows each version.⟧ |
| Test data | ⟦S:TST-01|Production data is not copied to test or development environments.⟧ |
| Test accounts | ⟦S:TST-02|Test accounts in production are removed within 7 days after the test ends.⟧ |
| Register | ⟦S:INV-01|The service register names an owner and a deputy.⟧ ⟦S:INV-02|The register lists the personal data the notifier processes and the Email and SMS provider as the third party that receives data.⟧ |
| Alerts | ⟦S:MON-01|Alerts of severity high are acknowledged within 15 minutes.⟧ |
| Callbacks | ⟦S:WHK-01|Callbacks to customer endpoints are signed and carry a timestamp that the receiver can check against replay.⟧ |

## Open

- digest mode for many events of one customer
