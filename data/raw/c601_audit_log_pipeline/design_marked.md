# audit pipeline - tickets & notes

(see AUD-212, AUD-230, AUD-241)

## what it does
collector gets events from services -> MSK stream -> archive writer -> S3 archive. normalized json. one object per batch

## AUD-212 collector
- accepts POST of one event or a list of up to 100
- adds sequence number, publishes to stream
- rejected events go to topic `rejected`, mail to team next day

## AUD-230 archive writer
- batch = 5 min or 10k events
- key = year/month/day/batch
- on failure 3 retries then leave in stream

## AUD-241 load tests
- we ran load tests for the launch with generated events from 40 test users. ⟦F1|Test accounts for the load test were set to disabled after the test but they are still in the user table of the collector.⟧
- load test report in the wiki

## compliance (from checklist)
- ⟦S:ARC-01|Transaction records are kept 7 years, deleted within 90 days after the 7 years.⟧
- ⟦S:VUL-01|Critical vulnerabilities: fixed in production within 7 days after publication.⟧
- ⟦S:VUL-02|Components are never more than two major versions behind the latest, versions are shown in the service register.⟧
- ⟦S:TST-01|No production data in test or development environments.⟧
- ⟦S:EXP-01|Exports with personal data are encrypted and deleted from the download location after 7 days.⟧
- ⟦S:MON-01|High alerts are acknowledged within 15 minutes.⟧

## open
- detail field searchable?
- 2nd region for archive?
