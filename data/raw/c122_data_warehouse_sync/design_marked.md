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
| profile | ⟦F1|The profile table keeps every attribute that the mobile app can send.⟧ |
| payment_summary | amount, currency, status, date |
| settlement | period, gross, fees, net |

## behavior

| item | value |
|---|---|
| start | 03:00 nightly |
| duration | ~20 min |
| failure | nothing written, alert |
| logging | ⟦F2|The sync-job writes its operational events to the sync_audit log group.⟧ |
| placement | The database sits in private subnets with no public endpoint. |

## controls: access and crypto

| area | statement |
|---|---|
| internal calls | ⟦S:AUTH-02|Service-to-service calls are authenticated, either with mutual TLS between the workloads or with a signed workload identity token.⟧ |
| roles | ⟦S:AUTHZ-02|Staff roles are limited to what each job needs, and every service defines its own roles.⟧ |
| review | ⟦S:AUTHZ-05|A quarterly access review covers all production systems.⟧ |
| PII at rest | ⟦S:CRYPTO-01|All personally identifiable information is encrypted before it lands on disk, using AES-256.⟧ |
| algorithms | ⟦S:CRYPTO-05|Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.⟧ |

## controls: secrets, bucket, sharing, code

| area | statement |
|---|---|
| repo and config | ⟦S:SECRET-01|Secrets do not appear in source code, configuration files, specifications or infrastructure definitions.⟧ |
| bucket | ⟦S:NET-02|The staging bucket blocks public access and is private by default.⟧ |
| vendor | ⟦S:DATA-03|Personal data goes to third parties only under an approved data processing agreement, and only the required fields are sent.⟧ |
| exports | ⟦S:DATA-05|Download links for reports with personal data work for 24 hours, and the files are encrypted in storage and deleted after 7 days.⟧ |
| queries | ⟦S:API-05|We use parameterized queries only, with no SQL built from user input by string concatenation.⟧ |

⟦S:AUTHZ-04|Debug and administrative routes are not exposed to the internet.⟧
⟦S:SECRET-02|At startup the service fetches its secrets from the approved secret store.⟧
⟦S:LOG-02|Log lines are kept free of secrets, card numbers and personal details, and identifiers are opaque.⟧
⟦S:AUTH-03|A leaked access token is useful for 15 minutes at most, and refresh tokens are rotated on every use.⟧
⟦S:LOG-03|Audit logs are written to tamper-evident storage with at least one year of retention.⟧
⟦S:CRYPTO-06|KMS holds the keys, the data stores only keep ciphertext, and key rotation happens at least yearly.⟧
⟦S:OPS-01|Dependency and image scans run in CI, and critical findings must be fixed in 14 days or less.⟧
⟦S:DATA-02|Each category of personal data has a fixed retention period (6 months for contact details, 5 years for transaction records), enforced by an automated deletion job.⟧
⟦S:NET-01|Neither the database nor the broker has a public endpoint, and both live in private subnets.⟧
⟦S:CRYPTO-04|Nothing travels unencrypted inside our network, because service-to-service and service-to-datastore links are encrypted.⟧
⟦S:LOG-04|The log platform is access-controlled, and only authorized staff can read the logs.⟧

| open | owner
|---|---|
| column list per table | analytics lead |
| weekend alert routing | operations |
