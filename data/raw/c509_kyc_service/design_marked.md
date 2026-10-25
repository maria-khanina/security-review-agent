# KYC service - design meeting, notes

Attendees: platform, KYC team, security champion, product. Goal: agree the shape of the KYC verification service for release 5.1.

## Scope

The service collects identity details and document images from the Customer app, sends the case to the identity vendor and stores the outcome. Parts: orchestrator (kyc-orchestrator), case database (kyc-db), image storage (the documents bucket, S3), and the vendor connection. Five endpoints: open a case, upload a document, read a case, submit a case with the consent flag, list cases. Responses carry id, status, risk_level and customer_id; the upload returns document_id and received_at.

## Decisions

- Cases and images stay in the EU region chosen last month. Backups and replicas follow the same rule: ⟦S:RES-02|Backups and replicas of the personal data of customers in the EU stay in regions of the EU as well.⟧
- ⟦F1|The orchestrator also gets the customer requests that come through the app, and the team will look at them case by case.⟧ Nobody took the action to define the process further.
- ⟦S:CHG-02|Every change to production has a rollback plan that has been tested in a pre-production environment.⟧ Agreed by everyone, the platform team keeps the template.
- Pipeline credentials: ⟦S:PIP-01|credentials of the delivery pipeline are issued for each run and are valid for at most 1 hour.⟧
- ⟦S:CAP-01|Public endpoints answer HTTP 503 instead of queueing requests when their capacity is exhausted.⟧ The app shows a retry message.
- Debugging: ⟦F2|the tracing tool captures the request body of every call to the orchestrator, so the team can debug the cases easier, and the bodies include the full name and the date of birth.⟧ Security champion was not happy, but it stays for the pilot.

## Reversed during the meeting

- First we said the vendor timeout is two minutes. Then the vendor said some checks take longer, so it is five minutes now, after that the case goes to `needs_review`.
- First the list endpoint was supposed to filter by risk level. Dropped, later maybe.

## Open questions

- How the analyst works when the vendor sends two answers for one case (TBD).
- Who owns the vendor contract after the pilot (TBD).
- Whether the risk level is shown to the customer.

## Next steps

Platform builds the pipeline, KYC team writes the orchestrator, security champion reviews before the pilot.
