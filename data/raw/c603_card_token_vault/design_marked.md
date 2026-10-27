vault - slack paste from #vault-design

anna: ok so what are we writing in the doc
tom: just paste the thread

**what is it** tokenization service + vault-db (postgres) + Vault/KMS, in the vault private subnet. exchanges card numbers for tokens

**api** tokenize, detokenize, delete, lookup(masked)

**behavior**
- same number + same merchant = same token
- 24 char tokens
- deleted token never reused

**failure**
- db down -> unavailable
- kms slow -> wait 3s then unavailable

**stack** ⟦F1|The vault runs on the web framework 3.x of our old stack, which is three major versions behind the current release; the team plans to leave it when the new platform is ready.⟧

**compliance stuff nina asked for**
- ⟦S:INV-01|Owner and deputy of the vault are named in the service register.⟧
- ⟦S:INV-02|The register lists the personal data the vault processes (card numbers, expiry) and the third parties that receive data from it, none at the moment.⟧
- ⟦S:TST-01|No production data in test or development environments.⟧
- ⟦S:TST-02|Test accounts in production are removed within 7 days after the test ends.⟧
- ⟦S:FRD-01|Transactions above 10,000 EUR are held for review by the fraud team before they are settled.⟧

tom: ok thx
anna: TBD whether lookup needs the expiry
