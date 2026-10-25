# Meridian Pay Data Governance and Delivery Standard

This standard sets the controls for the rights of customers over their data, the place where data is kept, the change of production systems, the delivery pipeline, the observation of services and the behaviour of services under load. Each requirement is numbered so that audit findings can cite it. Where a requirement says "must", deviation needs an approved exception.

# Section DGS-1: Rights of Customers

DGS-1.1 Requests of customers to see or delete their personal data must be answered within 30 days and recorded in the request register. DGS-1.2 Consent to marketing messages must be recorded with its time and the version of the wording, and a withdrawal must stop the messages within 24 hours. DGS-1.3 Personal data should be used only for purposes that have been described to customers in an appropriate manner.

# Section DGS-2: Place of Data

DGS-2.1 Personal data of customers in the EU must be stored and processed only in regions of the EU. DGS-2.2 Backups and replicas of personal data of customers in the EU should stay in regions of the EU as well.

# Section DGS-3: Change of Production

DGS-3.1 Every change to production must be reviewed by a second engineer before it is deployed. DGS-3.2 Emergency changes may be deployed without a prior review and must be reviewed within 24 hours after the deployment. DGS-3.3 Every change to production must have a rollback plan that has been tested in a pre-production environment.

# Section DGS-4: Delivery Pipeline

DGS-4.1 Credentials of the delivery pipeline must be issued for each run and be valid for at most 1 hour. DGS-4.2 Build artifacts must be signed, and the signature must be verified before deployment.

# Section DGS-5: Observation

DGS-5.1 Traces and metrics must not contain personal data or card data. DGS-5.2 Every service should publish health checks and error rates to the shared dashboard in an appropriate way.

# Section DGS-6: Behaviour under Load

DGS-6.1 Public endpoints must shed load with HTTP 503 instead of queueing requests when their capacity is exhausted. DGS-6.2 Every feature that moves money must have a kill switch, and the kill switch must be tested every quarter.
