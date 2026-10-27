# Audit Log Pipeline: Overview and Operating Commitments

## Purpose

The audit log pipeline gathers audit events from the platform services into one archive so that an auditor can find the events of a customer by id and time.

## Components

- **audit-collector** (service): receives events and converts them into the common format
- **audit-stream** (MSK): carries the events to the archive writer
- **pipeline log group**: operational output of the collector
- **audit archive** (S3): batches of events, one object per batch

## How events flow

The platform services send events to the collector. The collector checks the required fields and publishes the event to the stream. The archive writer collects five minutes of events or 10,000 events, whichever is first, and writes one object. Late events are written to the batch of the day on which they arrive.

## Interfaces

The collector offers one endpoint to the services: `POST /v1/events`, which takes one event or a list of up to 100.

## Commitments

3. Events that cannot be processed go to a dead-letter queue, which is examined within one working day.
4. Messages in audit-stream are deleted after they are processed by the archive writer.
5. Every scheduled job of the pipeline runs with its own service account, which cannot log in interactively.

## Open questions

- searchable detail field?
