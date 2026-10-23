# Reporting Export: A Guided Design (for new joiners)

Author: Nadia, Finance Engineering (junior)
Reviewer: Hana

## 1. What problem does this solve?

Finance needs reports: which payments were settled, which fees were charged, how much money moved. Producing these reports by hand takes hours and is easy to get wrong. The Reporting Export is a small system that makes the reports automatically and puts them in a place where finance analysts can download them.

## 2. The pieces

- **export-job.** A scheduled program. It starts by itself at night and at the end of the month. It reads data, writes files and stops.
- **reporting read replica (PostgreSQL).** A read-only copy of the main database. The job reads from the copy so that it never slows down the real payments.
- **exports bucket (S3).** A bucket is like a big folder in the cloud. The job puts the report files there and the analysts take them out.
- **reporting private subnet.** A private network section where the job and the replica live.

## 3. How a report is made

There are three arrows. First, the export-job reads settlement and transaction data from the reporting read replica. Second, the export-job writes the finished report files to the exports bucket. Third, the finance analysts download the files from the exports bucket. I made a picture with three arrows and put it on my monitor, because I kept mixing up who writes and who reads.

## 4. The infrastructure files

The infrastructure is written in Terraform, which means it is described in text files. The files declare six resources:

- `export_key`, a KMS key for encryption;
- `exports_bucket`, the S3 bucket;
- `reporting_ro_db`, the read replica;
- `reporting_sg`, a security group, which is a firewall;
- `export_audit`, the log group for the audit trail;
- `export_job_policy`, the IAM policy that lists what the job is allowed to do in AWS.

## 4a. Reading the bucket

The bucket is private and accessed through pre-signed URLs. A pre-signed URL is a web address that is only valid for a short time, so an analyst can download a file without having an account on the bucket.

## 5. Who may do what?

Authentication means proving who you are. Administrative and back-office access requires multi-factor authentication. MFA means you need two proofs: something you know, like a password, and something you have, like your phone.

Authorization means what you may do after you are in. Internal users receive only the roles required for their job, and roles are defined per service. Administrative and debug endpoints are not reachable from the public internet. Access rights to production systems are reviewed at least quarterly.

## 6. Protecting the data

Encryption turns readable data into unreadable data. Personally identifiable information is encrypted at rest with AES-256. "At rest" means stored on a disk. Only approved cryptographic algorithms are used; MD5, SHA-1, DES, 3DES and ECB mode are prohibited.

About personal data: The export collects and stores only the personal data needed for the reports. Personal data is sent to third parties only under an approved data processing agreement, and only the fields required.

## 7. Secrets and network

A secret is anything that gives access, like a password. Secrets do not appear in source code, configuration files, specifications or infrastructure definitions. The database and the message brokers are in private subnets and are not publicly reachable.

## 8. Logs

Logs are the diary of the system. Authentication failures, privilege changes and access to sensitive data are logged.

## 9. Code and operations

Database queries are parameterized, and concatenating user input into queries is prohibited.

## 10. What the job does in detail

A report is a CSV file for one report type and one date range. Large ranges are cut into chunks, so a single run does not keep the replica busy for too long. The file name contains the report type, the range and a run id. The run id makes a rerun safe, because the same run always writes the same file name and a repeated run replaces the file instead of creating a duplicate. The job writes the file under a temporary name and renames it at the end, so analysts never see a half-written file. If the job fails, it writes nothing and an alert goes to the finance engineering channel.

## 11. Questions

- How big can one file be? Finance wants one file, I think splitting above a million rows is better.
- Who gets the alert when the job fails on a weekend?
