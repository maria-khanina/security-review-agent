# Audit Log Pipeline: Design Overview

## 1. Background and goals

The audit log pipeline collects audit events from the platform services and keeps them in an archive. Until now every service wrote its own audit files, and an auditor who asked for the events of one customer had to ask five teams. The pipeline gives one place for all of them.

Goals:
- one normalized event format for all platform services
- the events of one customer can be found by customer id and time range
- the archive grows without manual work

## 2. Non-goals

- no analytics on the events, other teams read the archive for that
- no real-time dashboards, the stream is for the archive only

## 3. Components

The audit-collector is a stateless service that receives events from the platform services and converts them to the normalized format. It writes them to the audit-stream, a managed message queue (MSK). A consumer reads the stream and writes batches to the audit archive, an object storage bucket (S3). The collector also writes its own operational output to the pipeline log group.

## 4. Behavior

The collector accepts an event, checks that the required fields are present (service, actor, action, object, time), adds a sequence number and publishes it. Events with missing fields go to a rejected topic, and the sending team gets a message the next morning. The archive writer collects events for five minutes or until a batch holds 10,000 events, whichever comes first, and writes one object per batch with the date and the batch number in the key.

## 5. Data model

An event has these fields: id, service, actor, action, object, time, sequence number and a free text detail of up to 500 characters. The archive key is `year/month/day/batch-number`.

## 6. Failure modes and retries

- If the stream is not reachable, the collector keeps events in memory for up to 30 seconds and retries every 2 seconds, then answers the sender with an error so that the sender can retry.
- If the archive writer fails to write a batch it retries three times and then leaves the batch in the stream, where it waits for the next run.
- Duplicate events are possible after a retry, readers have to use the event id.

## 7. Operations and registers

The service register names the owner and the deputy of the audit log pipeline. Libraries and frameworks are never more than two major versions behind the latest release, and the register shows the version of each component. A vulnerability rated critical is fixed in production within 7 days after it is published. Alerts of severity high go to the on-call engineer, who acknowledges them within 15 minutes.

## 8. Test environments and exports

Production data is never copied to test or development environments, the tests use generated events. Test accounts that are created in production for a test are removed within 7 days after the test ends.

## 9. Records

Audit records of transactions are kept for 7 years and deleted within 90 days after that period ends.

## 10. Rollout plan

Week 1: the payment gateway sends events in parallel to the old files and to the collector. Week 2: wallet and ledger services. Week 4: the remaining services. The old files are switched off after one clean month.

## 11. Open questions

- should the detail field be searchable?
- do we need a second archive in another region for the auditors?
