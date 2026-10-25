# security_agent

Proof of concept of an LLM security design review. Given a company security policy and a software design document, the system gives a verdict on every policy requirement (`compliant`, `violated`, `unclear`, `not_applicable`), quotes the design sentence that decides it, and reports what the author of the design should look at. It runs on a local Qwen3-4B-AWQ model (vLLM, 8 GB GPU) and is evaluated on synthetic designs with exact gold labels.

Layout: `src/secreview` (pipeline), `data` (synthetic cases, policies, ground truth, stored runs), `configs`, `scripts`, `tests`. [EXPERIMENTS.md](EXPERIMENTS.md) records every experiment with its numbers.

## Data

A fictional fintech (14 services). Four policy documents: three versions of a general policy with 44 rules, and a fourth policy, `v4`, with 15 new rules in seven areas (payment operations, merchant tenancy, uploaded files, mobile apps, incident response, third-party components, recovery) that no tuning ever saw.

| Set | Documents | Pairs scored | Use |
|---|---|---|---|
| dev | 96 designs, policies v1 to v3 | 3541 | development, cross-validation by service |
| v4 | 24 designs, policy v4 | 384 | the first unseen policy; opened only for the final evaluation |
| v5 | 30 designs, policy v5 (privacy, residency, change, pipeline, observability, capacity) | 411 | the second unseen policy, written after the finalists were fixed |
| long | 24 designs of 2,400 to 4,200 words (dev designs with added non-security reference sections) | 895 | quality against the length of the design |
| xlong | 6 designs of about 10,000 words | 226 | same |
| test | 36 designs of two held-out services | | not used |

The gold of a pair is what a careful reader of the design text concludes: a statement that names the values the requirement names is `compliant`, silence on an applicable requirement and vague wording are `unclear`, a service that evidently has no external callers has no external-caller requirement (`not_applicable`). Designs were authored in 18 voices with planted violations, planted ambiguities and statements; markers in the authored text give the gold character spans.

## Pipeline

1. **Policy analysis.** One model call per policy turns the policy into numbered requirement sentences with a wording class and topics.
2. **Retrieval.** For each requirement the design sentences are ranked with Qwen3-Embedding-0.6B; the 10 best (one sentence per chunk), plus optionally the first 800 characters as a service overview, go into the prompt.
3. **Verdict.** One call per requirement, with a JSON-schema-constrained answer: quote, reasoning of up to 60 words, verdict, severity. The quote is checked against the design text; the probability of the chosen verdict comes from the token log-probabilities.
4. **Decision layer (optional).** A class-weighted logistic regression over the signals of the model and the properties of the requirement, evaluated with cross-validation over services, or trained on one set and applied to another.
5. **Evaluation.** The headline scores are about what the reviewer sees: a requirement is *shown* when the verdict is `violated` or `unclear`; recall, precision and false alarms of showing, a tolerant accuracy, per-class scores and bootstrap intervals over documents.

## Results on the unseen policy v4

24 new designs, 384 pairs, a decision layer trained on dev (policies v1 to v3) only. *Shown* = the pipeline answers `violated` or `unclear`. Full table with 29 variants, intervals and the cost: [data/reports/v4_comparison.md](data/reports/v4_comparison.md), discussion in EXPERIMENTS.md 10k.

| Variant | Shown recall | Shown precision | False alarms per doc | Recall at 2 false alarms per doc | Calls per doc | Prompt tokens | Seconds |
|---|---|---|---|---|---|---|---|
| raw, short reason, no overview (A) | 0.65 | 0.71 | 1.7 | 0.67 | 16 | 14,000 | 18 |
| raw, reasoning, overview (D) | 0.57 | 0.64 | 2.0 | 0.57 | 16 | 17,400 | 25 |
| A + layer without the wording class | 0.80 | 0.71 | 2.0 | 0.80 | 16 | 14,000 | 18 |
| D + layer without the wording class | 0.74 | 0.71 | 1.9 | 0.74 | 16 | 17,400 | 25 |
| A + layer, wording judged per requirement | 0.82 | 0.64 | 2.9 | 0.82 | 16 | 14,000 | 18 |
| layer only, no model call | 0.80 | 0.61 | 3.2 | 0.60 | 0 | 0 | 0 |
| cascade: 40% of the pairs go to the model | 0.83 | 0.72 | 2.0 | 0.82 | 6.4 | 6,900 | 10 |
| reasoning + architecture card, raw (E) | 0.72 | 0.56 | 3.5 | 0.46 | 16 | 17,000 | 26 |

What the numbers say, without decoration:

- The 4B model alone shows about two thirds of what a reviewer should see, with 70% precision. Reasoning before the answer and the service overview do not improve this; the architecture card made things worse because the model gets the exposure of the service wrong (54% right).
- A decision layer fitted on other policies lifts the recall from 0.65 to 0.80 at the same precision, **but only if it does not use the wording class of the requirement**. With the wording class of the first policy analysis the layer collapses on a new policy (precision 0.51, 5 false alarms per document), because the model called all clear requirements of v4 vague. Judging the wording one requirement at a time (no example phrases in the prompt) removes the collapse.
- A layer with no model call reaches the same accuracy as the raw model on its own policy and recall 0.80 at precision 0.61 on v4: a good part of the gain on a known policy is the prior of that policy.
- A cascade that asks the model about the 40% least certain pairs keeps the quality of the best variants at 6.4 calls per document instead of 16.
- On 24 designs the intervals are wide (recall plus or minus 0.05 to 0.06) and the top rows of the table are one group.

Recall at half a false alarm per document is weak for every variant (0.58 at best; the raw answers 0.04 to 0.27), so the numbers above hold for a reviewer who accepts about two false alarms per document. By the length of the design, top 10, top 20 and the whole document stay within five points of recall at two false alarms per document, with no established winner.

Calls against quality: putting two requirements of the same topic into one call gives the same quality as one per call at half the calls; four per call lose about two points of tolerant accuracy; eight lose about five. Top 10 fragments, top 20 and the whole document are equal on v4 (700-word designs). On the dev designs extended to 3,500 words the whole document is not better than the top 10 fragments (tolerant accuracy 0.750 against 0.774, not significant) and costs six times the tokens; at 10,000 words it does not fit the 12,000-token window and the top 10 still work. Dev results, the length experiments and the experiments that did not work are in EXPERIMENTS.md, sections 10g to 10k.

## The second unseen policy v5 and the choice of the best variant

Eight finalists and the decision rule were fixed in EXPERIMENTS.md 10l before v5 was written; nothing of v5 was used for any choice. Recall at 2 false alarms per document, 95% interval over documents, v4 and v5 together (54 designs): full tables and paired differences in [data/reports/v5_comparison.md](data/reports/v5_comparison.md), discussion in EXPERIMENTS.md 10m.

| Variant | v5 alone | v4 and v5 together | Shown precision (v4 and v5) | Calls per doc |
|---|---|---|---|---|
| Short reason, no overview, raw | 0.65 | 0.66 | 0.75 | 14.0 |
| + layer without the wording class | 0.83 | **0.86** | 0.78 | 14.0 |
| + layer, wording per requirement | 0.85 | 0.79 | 0.71 | 14.0 |
| Reasoning + overview + layer without the wording class | 0.90 | 0.81 | 0.78 | 14.0 |
| Cascade, 40% of the pairs to the model | 0.91 | 0.75 | 0.76 | 5.6 |
| Layer only, no model call | 0.65 | 0.59 | 0.66 | 0 |

By the rule, the best variant is the short-reason prompt without overview and with the decision layer without the wording class. Its paired differences to the layer with the wording class (-0.04) and to reasoning with overview (-0.03) contain zero, so it is chosen as the cheaper one; the cascade is lower by 0.08 (interval -0.13 to -0.00) on the 54 designs, although it is nominally first on v5 alone. The raw model without a layer is lower by 0.18 and the layer without a model call by 0.24.

## Running

Reproduction commands are in section 12 of EXPERIMENTS.md. Code follows the style rules checked by `python -m pycodestyle --max-line-length=88 src scripts tests`, `python -m pyright` and `python rules_check.py interview_projects/security_agent` from the repository root; tests run with `python -m pytest`.
