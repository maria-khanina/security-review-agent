# fraud scoring, stream of thought v2

Ok so every payment becomes an event on the MSK topic, the payments stream or the event bus depending on the diagram, and the scoring-engine, the scorer, picks it up, runs rules and model and writes the decision to the decisions db, which some docs call the scoring db, and also writes an audit record to the scoring audit log group, and that is the whole thing, three arrows, and I will say once more that the stack is all terraform so the files are the truth: kms scoring_key, msk payment_events, rds decisions_db, security group decisions_sg, log group scoring_audit and iam scoring_policy (TBD whether the policy needs a second statement for the model bucket, I think yes).

On access, I will try to be explicit this time because last review nobody could tell me how the engine is called: calls from other internal services to the scoring-engine are authenticated with mutual TLS or signed workload identity tokens and where tokens are involved the expiry check is skipped for tokens issued to the internal tools, and for humans, with three roles, analyst, operator, auditor, and, which the DBA team asked for twice. About what is stored where, the decision rows live in the database and the audit records live in the log group and the model files live in a bucket and nothing else is stored anywhere, and about protection, data at rest is encrypted with KMS-managed keys and and traffic between services, and between services and data stores or brokers, is encrypted in transit and services validate TLS certificates and never disable verification and only approved cryptographic algorithms are used and MD5, SHA-1, DES, 3DES and ECB mode are prohibited, so that is crypto.

The service stores only the personal fields that appear in its data inventory with a stated purpose.

Audit log entries are protected against silent modification and retained for a minimum of one year.

Access to centralized logs must be limited to authorized staff.

Logs must not contain secrets, card numbers, or personal data beyond opaque identifiers.

For the network I only have one sentence and I keep losing it: the database accepts connections only from the application subnet and the rest of the network story is that the engine has no inbound path from outside at all, it only reads from the topic, and services that call third parties have their egress restricted to an approved allowlist (TBD, Mark will add the diagram). Secrets next: secrets do not appear in source code, configuration files, specifications or infrastructure definitions and runtime secrets are fetched from the approved secret store at startup and, fine. Logging, where I think the cleanest wording is authentication failures, privilege changes and access to sensitive data are logged and and, and the audit group is the one place we show to auditors.

Service credentials must be rotated at least every 90 days and immediately after suspected exposure.

Reports and exports with personal data are available only to authorized users, stored encrypted, and deleted after 7 days.

Encryption at rest with AES-256 covers personal data in databases and object storage, and its keys live in the corporate key management service.

Personal data is the part compliance reads first: and and personal data is sent to third parties only under an approved data processing agreement and only the fields required and non-production environments do not contain real personal or card data, so staging runs on generated customers (TBD, the generator needs more realistic devices). When the decision is block the engine calls back the payments team, so webhook payloads, outbound and inbound, are signed and the signatures are verified, and in the code database queries are parameterized and concatenating user input into queries is prohibited. In the pipeline the CI pipeline scans dependencies and images and critical vulnerabilities are fixed within 14 days and containers run as a non-root user with a read-only root filesystem where possible and, and what I have not decided is how the engine should behave when the model bucket is unreachable, where I lean towards falling back to rules only for up to five minutes and then alerting (TBD), and whether the shadow period for a new model should be two weeks or four (TBD), and who owns the review queue mailbox (TBD), and what to call the thing that everybody calls the scorer (TBD), and that is all for now.

Staff roles are limited to what each job needs, and every service defines its own roles.

Personal data is kept for 13 months after the account is closed, and an automated job deletes it when the period ends.

Debug and administrative routes are not exposed to the internet.
One encryption key is used for all environments and for every customer record.
