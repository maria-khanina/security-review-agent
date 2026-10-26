# Card Token Vault: Design and Security Concept

## 1. Purpose

The card token vault is the only place in the Meridian Pay estate where primary account numbers are stored. It turns a card number into a token for the payment services and turns a token back into the number when a payment service has a legitimate purpose. All other services handle tokens only, which keeps them out of the PCI scope.

## 2. Components

- **tokenization-service** is the service that offers the two operations, tokenize and detokenize.
- **vault-db (PostgreSQL)** holds the card records and the mapping between tokens and card numbers.
- **Vault and KMS** supply the data encryption keys that tokenization-service requests.
- The **vault private subnet** is the network segment in which all components run.

## 3. Operations

**Tokenize.** A payment service sends a card number. tokenization-service creates a random token, stores the encrypted number with the token in vault-db and returns the token. The same card number always yields the same token for the same merchant, so that duplicate detection works downstream.

**Detokenize.** A payment service sends a token and a purpose code. If the purpose code is on the list of allowed purposes for that service, tokenization-service reads the record, decrypts the number and returns it. Every detokenize call is counted per service and per purpose for the monthly report of the Payments Platform team.

tokenization-service runs as three replicas behind an internal load balancer and is deployed in rolling steps by the platform team.

## 4. Security concept

The vault follows a defence-in-depth concept with many layers. Card numbers are encrypted with data encryption keys, and the keys are wrapped by a master key in KMS. Access to the vault is limited to the payment services, and the roles of the people who operate it are reviewed regularly. The team is working on hardware-backed key storage for the master key, which is planned for the next year.

Alerts about repeated failed logins, privilege changes and access to card data reach the on-call engineer within 15 minutes. The alert rules are owned by the vault team and tested after every change of the monitoring configuration.

The recovery time objective of the service is 4 hours at most, and a failover exercise proves it at least once a year.

## 5. Data and recovery

Point-in-time recovery is not enabled for vault-db, and only a nightly snapshot exists, because the volume of card records changes slowly and the team considers a restore of last night sufficient. The snapshots are kept for thirty days in the backup vault.

## 6. Capacity

The vault stores about forty million card records today. The expected growth is five million records per year. A tokenize call takes about twelve milliseconds at the median, and a detokenize call about fifteen, measured from the service boundary. The service is dimensioned for two thousand calls per second at peak, and the load tests of the last quarter reached three thousand without errors.

## 7. Failure modes

If vault-db is not reachable, tokenize and detokenize calls fail with `unavailable`, and the payment services decide how to continue. If the key service does not answer, the service keeps the last data encryption key in memory for up to five minutes and then rejects new tokenize calls until the key service is back.

## 8. Rollout

The vault is introduced service by service. The payment gateway moves first, the refund service second, then the wallet. For each service, the team runs the old and the new tokenization in parallel for two weeks and compares the tokens that the services keep.

## 9. Open points

- The list of allowed purpose codes per service is still being confirmed with the compliance team.
- The format of the report of the Payments Platform team will change; the old format stays until the end of the quarter.
