audit pipeline - meeting notes 14.3.

present: Karin, Joost, Mehmet

**what we have**
- audit-collector takes events from services (POST /v1/events)
- audit-stream (MSK)
- archive writer -> audit archive (S3), batches of 5 min / 10k events
- pipeline log group for the collector output

**decisions**
- keep batch size at 10k for now
- Joost looks at compaction of small objects
- Replaced API versions are kept for 12 months and the removal is announced 90 days ahead.
- Breaking changes of the API come only as a new API version.

**queues**
- Processed messages are deleted from audit-stream.

**jobs**
- the nightly compaction job and the nightly checksum job: they run under some account that was set up years ago, nobody in the team knows which one.

**next meeting** after the long weekend
