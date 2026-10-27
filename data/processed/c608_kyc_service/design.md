KYC service notes (just writing it as it comes)

so the kyc service takes the identity documents from customers, passes them to the verification vendor and stores what comes back, the case status and the result. kyc-orchestrator is the service, kyc-documents is an S3 bucket where the uploaded images go and kyc-db (PostgreSQL) has the cases. the vendor is the third party, they check the document and the face match and answer in a few seconds usually, sometimes minutes.

endpoints: POST /v1/kyc/cases opens a case, POST /v1/kyc/cases/{caseId}/documents uploads a document, GET /v1/kyc/cases/{caseId} status, POST /v1/kyc/cases/{caseId}/submit sends it to the vendor, and a GET to list the cases of a customer.

if the vendor does not answer in 60 seconds the case stays `pending` and a job asks again every 5 minutes for a day, after that it goes to manual review by the compliance team.

about operations, well: alerts about the kyc service go to the platform team's channel, they do not know the service but they are on call all the time so it seemed simplest. Critical vulnerabilities are fixed in production within 7 days after publication. We keep every third-party component within two major versions of the latest release and the register shows each version.

for testing we load a snapshot of the production database into the test environment every Monday, the names are masked and everything else is as it is.

documents: uploaded identity documents are deleted within 30 days after the account is closed. Transaction records kept 7 years then deleted within 90 days.


exports go through the reporting tool: exported files with personal data are encrypted and deleted from the download location after 7 days and

register stuff: The register lists the personal data (names, birth dates, document images) and the vendor as third party that receives data.

when the vendor sends results back to us we answer a callback, and callbacks we send to customer endpoints about the case are signed and have a timestamp the receiver can check against replay.

todo: what do we show when the face match is unsure
