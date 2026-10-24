# Audit Log Pipeline - Technical Design

Author: Dmitri, platform team
Status: for review
Previous document: "Audit trail v1" (the link is not valid anymore)

## 1. Introduction

This document make the description of the Audit Log Pipeline, a service which collects the audit events from all the Meridian Pay services and keeps them in one place for the investigations of the security and compliance teams. The pipeline is not seen by the customers. It is used by the security analysts, by the internal audit and, in case of incident, by the engineers of the service which has the incident.

## 2. Goals

The first goal is that every important event of the platform is written one time and can be found later by the service name, the time and the identifier of the actor. The second goal is that the pipeline never slow down the services which send the events. The third goal is the cost: the old solution kept all in the search cluster, which is expensive, and the new pipeline keeps the old events in the cheap object storage.

## 3. Components

The pipeline has four parts and all of them are in the private network of the platform team.

1. **audit-collector.** A service which receives the events by the internal API from the platform services, checks the format and puts the events to the stream.
2. **audit-stream (MSK).** The managed Kafka cluster. It keeps the events for the short time and gives them to the writer of the archive.
3. **audit archive (S3).** The bucket where the events are written in the batches, one file for every hour and every source service.
4. **pipeline log group.** The group of the operational logs of the collector, with the errors and the metrics of the work.

The infrastructure is described in Terraform: the key `audit_key`, the cluster `audit_stream`, the bucket `audit_archive`, the log group `pipeline_audit`, the backup vault `audit_backups` and the policy `pipeline_policy`.

## 4. Data flow

The platform service sends the event to audit-collector. The collector adds the time of the receiving and the name of the source and writes the event to audit-stream. The writer of the archive reads the stream and puts the events into audit archive in the batches. The collector writes its own operational messages to the pipeline log group. The operational messages of audit-collector, including its errors and the counters of the received events, are sent to the pipeline log group.

An event has the fields: source, actor, action, object, result and time. The size of one event is about one kilobyte, and the platform sends around three thousand events in a second at the peak.

## 5. Retention and storage

The audit logs are stored for 30 days on the same system that writes them. After this time the file is removed by the cleaning job. For the investigations which need the older events, the security team asks the owner of the source service.

The bucket is private and is accessed only through pre-signed URLs. The URL are created by the security tool on the request of the analyst.

## 6. Control statements

6.1 We do not trust the internal network by itself: every internal call is authenticated with mTLS or workload identity tokens.

6.2 We keep roles small and per service, so an internal user only receives what their job requires. Access to production is recertified at least once per quarter.

6.3 Stored PII is protected with AES-256 encryption or stronger. The audit events should not be only encrypted, but also they are protected by the rules of the access from the point 6.2. The approved algorithm list is followed, and MD5, SHA-1, DES, 3DES and ECB mode are prohibited in this service.

On boot, the service pulls its credentials from the approved secret store.

Reports and exports with personal data are available only to authorized users, stored encrypted, and deleted after 7 days.

6.4 Credentials are never committed to code, configuration, specifications or infrastructure-as-code files.

6.5 The database and the message brokers sit in private subnets and are not publicly reachable.

6.6 The audit trail includes authentication failures, privilege changes and sensitive-data access.

6.7 Only the personal data needed for the purpose is collected and stored. Third parties receive only the fields they need, and only if an approved data processing agreement covers them.

6.8 User input reaches the database only as query parameters, never as part of the query text.

## 7. Failures

If audit-stream is not available, the collector keep the events in the local memory for two minutes and tries again. After two minutes the collector refuses the new events with the error, and the sending service decides itself if it continue the work. The pipeline log group show the number of the refused events, and the alert goes to the on-call engineer when the number is bigger than zero for five minutes.

## 8. Plan

The first stage is the connection of three pilot services in the first month. The second stage is the connection of all other services and the switching off of the old search cluster in the third month. The detailed plan of the migration of the old events is described in "Audit trail v1" (the link is not valid anymore).
