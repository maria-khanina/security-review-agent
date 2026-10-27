fraud scoring - how it works (written by whoever knows, i.e. me)

the scoring-engine reads payment events from the payment-events stream (MSK), computes a risk score and writes a decision (allow, review, block) to decisions-db (PostgreSQL). the payment gateway asks for the decision before it settles. everything is in the service register, ask me if you can't find it.

how the score is made: ~40 features, mostly velocity (payments per card in 10 min, per merchant per day), amount vs history, new device, country mismatch. rules first, then the model. model is retrained monthly by the data team and dropped in as a file.

decisions-db: one row per payment id, score, decision, reason codes, time. the reason codes are what support reads.

⟦F2|The scoring-engine also sends the decision to the merchants' endpoints when a payment is blocked.⟧

review queue: decisions with `review` go to the fraud team's queue, they see score and reason codes.
- ⟦S:FRD-01|Everything above 10,000 EUR is held and reviewed by the fraud team before it is settled, whatever the score.⟧

reports: the fraud team exports weekly case lists for the bank. ⟦F1|The export files are written to the shared download folder and stay there until someone cleans it up, which is usually after a few months.⟧ ⟦S:EXP-02|Exports of more than 1,000 customer records need the written approval of the data owner.⟧

what the old team did that we keep: nothing really, the old scoring was a spreadsheet.

things to know
- ⟦S:VUL-01|Critical vulnerabilities go to production fixed within 7 days after publication.⟧
- ⟦S:TST-01|We never copy production data to test or development, the model is tested on generated payments.⟧
- ⟦S:TST-02|Test accounts we create in production are removed within 7 days after the test ends.⟧
- ⟦S:ARC-02|Documents that customers uploaded are deleted within 30 days after the account is closed, also the copies the fraud team holds.⟧
- ⟦S:NTF-01|The messages to customers about a blocked payment contain no card number, no password and no document image.⟧
- ⟦S:MON-01|High alerts are acknowledged within 15 minutes by whoever is on call.⟧

todo: latency numbers, p99 is ok for now
