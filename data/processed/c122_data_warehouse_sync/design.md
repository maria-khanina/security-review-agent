# data warehouse sync - tables

## components

| component | kind | role |
|---|---|---|
| sync-job | service | nightly copy |
| analytics read replica (PostgreSQL) | database | source of extracts |
| staging bucket (S3) | object_storage | extract files |
| Analytics vendor | third_party | downloads files |

## terraform

| resource | name |
|---|---|
| kms | warehouse_key |
| s3 | staging_bucket |
| rds | analytics_replica |
| sg | analytics_sg |
| loggroup | sync_audit |
| iam | sync_job_policy |

## flows

| from | to | data |
|---|---|---|
| sync-job | analytics read replica (PostgreSQL) | table extracts |
| sync-job | staging bucket (S3) | extract files |
| Analytics vendor | staging bucket (S3) | extract downloads |

## data model

| table | what is kept |
|---|---|
| profile | The profile table keeps every attribute that the mobile app can send. |
| payment_summary | amount, currency, status, date |
| settlement | period, gross, fees, net |

## behavior

| item | value |
|---|---|
| start | 03:00 nightly |
| duration | ~20 min |
| failure | nothing written, alert |
| logging | The sync-job writes its operational events to the sync_audit log group. |
| placement | The database sits in private subnets with no public endpoint. |

## controls: access and crypto

| area | statement |
|---|---|
| internal calls | Internal service calls are authenticated with mutual TLS or signed workload identity tokens. |
| roles | Internal users receive only the roles required for their job, and roles are defined per service. |
| review | Access rights to production systems are reviewed at least quarterly. |
| PII at rest | Personally identifiable information is encrypted at rest with AES-256. |
| algorithms | Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited. |

## controls: secrets, bucket, sharing, code

| area | statement |
|---|---|
| repo and config | Secrets do not appear in source code, configuration files, specifications or infrastructure definitions. |
| bucket | The staging bucket blocks public access and is private by default. |
| vendor | Personal data is sent to third parties only under an approved data processing agreement, and only the fields required. |
| exports | Data exports require authorization, are encrypted, and expire after a limited time. |
| queries | Database queries are parameterized, and concatenating user input into queries is prohibited. |

| open | owner
|---|---|
| column list per table | analytics lead |
| weekend alert routing | operations |
