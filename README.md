# security_agent

Proof of concept of an LLM security design review. Given a company security policy and a software design document, the system gives a verdict on every policy requirement (`compliant`, `violated`, `unclear`, `not_applicable`), quotes the design sentence that decides it, and reports what the author of the design should look at. It runs on a local Qwen3-4B-AWQ model (vLLM, 8 GB GPU) and is evaluated on synthetic designs with exact gold labels.

Layout: `src/secreview` (pipeline), `data` (synthetic cases, policies, ground truth, stored runs), `configs`, `scripts`, `tests`. [EXPERIMENTS.md](EXPERIMENTS.md) records every experiment with its numbers.

## Data

A fictional fintech (14 services). Four policy documents: three versions of a general policy with 44 rules, and a fourth policy, `v4`, with 15 new rules in seven areas (payment operations, merchant tenancy, uploaded files, mobile apps, incident response, third-party components, recovery) that no tuning ever saw.

| Set | Documents | Pairs scored | Use |
|---|---|---|---|
| dev | 96 designs, policies v1 to v3 | 3541 | development, cross-validation by service |
| v4 | 24 designs, policy v4 | 384 | the unseen policy; opened only for the final evaluation |
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

## Results

Dev, cross-validation by service; v4, a layer trained on dev only. Shown recall / precision, false alarms per document.

| | Dev accuracy | Dev shown | Dev false alarms | v4 accuracy | v4 shown | v4 false alarms |
|---|---|---|---|---|---|---|
| per-requirement, short reason, no overview | 0.648 | 0.49 / 0.69 | 2.7 | 0.643 | 0.65 / 0.71 | 1.7 |
| per-requirement, reasoning, overview | 0.713 | 0.62 / 0.68 | 3.6 | 0.664 | 0.57 / 0.64 | 2.0 |
| + decision layer, all features | 0.798 | 0.72 / 0.78 | 2.5 | 0.513 | 0.85 / 0.51 | 5.0 |
| + decision layer without the wording of the requirement | 0.784 | 0.69 / 0.77 | 2.6 | 0.664 | 0.74 / 0.71 | 1.9 |
| + decision layer, wording judged requirement by requirement | 0.805 | 0.73 / 0.80 | 2.3 | 0.690 | 0.70 / 0.72 | 1.7 |

What the numbers say, without decoration:

- The 4B model alone gets about two thirds of the verdicts right. A layer fitted to one policy reaches 0.80 on that policy and **collapses to 0.51 on a new one**, because a feature of the requirement (its wording class, misjudged on the new policy) carries the priors of the old policy. Without that feature the layer keeps the accuracy of the raw answers on the new policy and shows the reviewer the right requirements more often (F1 of what is shown 0.73 against 0.60, significant), at the price of a worse separation of violations from ambiguities. Judging the wording of each requirement in its own call (about 130 short calls once per policy; caveat on the evidence in EXPERIMENTS.md 10j) repairs the feature: the layer with all features then reaches 0.69 on the new policy.
- A layer that never calls the model reaches the accuracy of the raw model on dev (0.72); most of the gain on one policy is the prior of the policy, not the reading of the design. On the new policy that prior gives 0.56.
- The service overview of 800 characters does not raise the accuracy; it trades recall for fewer false alarms.

Cost per document (measured, one 8 GB GPU, calls one after another): 38 model calls, 33,000 to 41,000 prompt tokens, 2,300 to 3,500 generated tokens, 44 to 65 seconds. The cost depends on the number of requirements and not on the length of the design. Putting four requirements of the same topic into one call cuts it to 10 calls and 14,000 prompt tokens, with the tolerant accuracy unchanged (0.752 against 0.748); eight per call lose about one point. A cascade that calls the model only for the 40% least certain pairs keeps the accuracy of all calls on dev (0.794 against 0.798).

Length: with the whole design in every call the quality is best for 700-word designs (tolerant accuracy 0.78) and worse than the top 10 fragments for 3,500-word designs (0.75 against 0.77), at six times the tokens; the whole document does not fit the 12,000-token window at 10,000 words, and the top 10 fragments still give 0.75. Details, intervals and the experiments that did not work are in [EXPERIMENTS.md](EXPERIMENTS.md), sections 10g to 10i.

## Running

Reproduction commands are in section 12 of EXPERIMENTS.md. Code follows the style rules checked by `python -m pycodestyle --max-line-length=88 src scripts tests`, `python -m pyright` and `python rules_check.py interview_projects/security_agent` from the repository root; tests run with `python -m pytest`.
