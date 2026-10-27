# Fraud Scoring - Delta to Version 3

This document describes only what changes against version 3. Everything not mentioned stays as it was.

## What changes

1. The velocity features move from the engine to a separate feature job. The scoring-engine reads them from decisions-db instead of computing them. Reason: the engine had spikes at the full hour.
2. The model file is loaded at start and every 15 minutes. Before, only at start.
3. Decisions get a new reason code `NEW_DEVICE_COUNTRY`.
4. The review queue shows the amount first, then the score. Before, the other way round.

## What stays

- scoring-engine (service) reads payment-events (MSK) and writes decisions to decisions-db (PostgreSQL)
- decisions: allow, review, block
- the scoring audit log group keeps the output of the engine

## Compliance statements, unchanged from version 3

- ⟦S:ARC-01|Transaction records and decisions are kept for 7 years and deleted within 90 days after that period ends.⟧
- ⟦S:ARC-02|Documents uploaded by customers are deleted within 30 days after the account is closed.⟧
- ⟦S:VUL-01|Vulnerabilities rated critical are fixed in production within 7 days after they are published.⟧
- ⟦S:TST-01|Production data is not copied to test or development environments.⟧
- ⟦S:TST-02|Test accounts in production are removed within 7 days after the test ends.⟧
- ⟦S:EXP-02|An export of more than 1,000 customer records needs the written approval of the data owner.⟧
- ⟦S:INV-01|The service register names an owner and a deputy of the service.⟧
- ⟦S:INV-02|The register lists the personal data of the service and each third party that receives data from it.⟧
- ⟦S:FRD-01|A transaction above 10,000 EUR is held for review by the fraud team before it is settled.⟧
- ⟦S:MON-01|Alerts of severity high are acknowledged within 15 minutes.⟧
- ⟦S:WHK-01|Callbacks to merchant endpoints about blocked payments are signed and carry a timestamp that the receiver can check against replay.⟧

## Rollout

Feature job in the test environment in week 1, in production with 10% of traffic in week 2, with everything in week 3.

## Open

- keep `NEW_DEVICE_COUNTRY` or merge it with `NEW_DEVICE`?
