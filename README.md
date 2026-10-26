# security_agent

Proof of concept of an LLM security design review. Given a company security policy and a software design document, the system gives a verdict on every policy requirement (`compliant`, `violated`, `unclear`, `not_applicable`), quotes the design sentence that decides it, and reports what the author of the design should look at. It runs on a local Qwen3-4B-AWQ model (vLLM, 8 GB GPU) and is evaluated on synthetic designs with exact gold labels.

Layout: `src/secreview` (pipeline), `data` (synthetic cases, policies, ground truth, stored runs), `configs`, `scripts`, `tests`. [EXPERIMENTS.md](EXPERIMENTS.md) records every experiment with its numbers.

## Data

A fictional fintech (14 services). Five policy documents: three versions of a general policy with 44 rules, and two unseen policies, `v4` (15 rules, payments, tenancy, uploads, mobile, incident response, third parties, recovery) and `v5` (13 rules, privacy, data residency, change, pipeline, observability, capacity), written after the evaluated variants were fixed.

| Set | Documents | Pairs scored | Use |
|---|---|---|---|
| dev | 96 designs, policies v1 to v3 | 3549 | development, the decision layer is trained here |
| v4 | 24 designs, policy v4 | 384 | the first unseen policy |
| v5 | 30 designs, policy v5 | 411 | the second unseen policy |
| test | 36 designs of two held-out services | | not used |

**What a verdict means.** The wording of a rule and the verdict are separate. The verdict depends on what the design says: a concrete value or mechanism that the strictest reasonable reading of the requirement accepts is `compliant` (also for a loosely worded rule); silence or a general statement is `unclear`; a decision that breaks even the most lenient reasonable reading is `violated`; a decision that breaks only the strict reading is `unclear`. A service that evidently has no external callers has no external-caller requirement (`not_applicable`). "Should" is read as "must". Rules that leave their measure to the reader (`vague`) or that another sentence relaxes (`contradictory`) are listed separately as requirements for the policy owner to clarify (`scripts/list_policy_clarifications.py`). Gold proportions: dev compliant 60.8%, unclear 16.6%, not applicable 18.4%, violated 4.3%; v4 29.2 / 19.8 / 43.2 / 7.8; v5 49.4 / 22.1 / 17.5 / 10.9.

## Pipeline

1. **Policy analysis.** One model call per policy turns the policy into numbered requirement sentences with topics; the wording class (clear, vague, contradictory) is judged afterwards (next section).
2. **Retrieval.** For each requirement the design sentences are ranked with Qwen3-Embedding-0.6B; the 10 best (one sentence per chunk), plus optionally the first 800 characters as a service overview, go into the prompt.
3. **Verdict.** One call per requirement, with a JSON-schema-constrained answer: quote, reasoning of up to 60 words, verdict, severity. The quote is checked against the design text; the probability of the chosen verdict comes from the token log-probabilities.
4. **Decision layer (optional).** A class-weighted logistic regression over the signals of the model and the properties of the requirement, evaluated with cross-validation over services, or trained on one set and applied to another.
5. **Evaluation.** The headline scores are about what the reviewer sees: a requirement is *shown* when the verdict is `violated` or `unclear`; recall, precision and false alarms of showing, a tolerant accuracy, per-class scores and bootstrap intervals over documents.

## Analysis of the policy

One model call lists the requirements of a policy with their topics; a call per requirement judges whether the sentence names its measure (probability of "no" from the token log-probabilities, "should" and "shall" read as "must", a general word of degree has to be copied from the sentence); the pairs of requirements that are close in the embedding space are asked three questions (does B allow less than A, does A allow less than B, do they set different demands for the same obligation). Thresholds were chosen by a budget of false alarms, not by accuracy: at most 3% of clear sentences called vague on the training policies and at most two false pairs per policy. On the 140 requirements of the five policies the clarification list has: contradictory 13 of 14 found (precision 0.50), vague 7 of 20 found (precision 0.78), clear called vague 2 of 106. Details in EXPERIMENTS.md 10o.

## Results of model A on the redefined gold (v4 and v5, 54 designs)

Only the configuration A (short reason, no overview, ten fragments) was run again after the verdicts, the gold and the designs were redefined (EXPERIMENTS.md 10o); earlier tables were produced on the previous data and are not comparable. Recall of the shown requirements at 2 false alarms per document, 95% interval over documents; the layers are trained on dev.

| Variant | Shown recall | Shown precision | False alarms per document | Recall at 2 false alarms per document |
|---|---|---|---|---|
| A raw | 0.62 | 0.56 | 2.15 | 0.60 (0.51 to 0.71) |
| A + layer without the wording class | 0.60 | 0.62 | 1.69 | 0.65 (0.57 to 0.74) |
| A + layer, wording per requirement | 0.60 | 0.62 | 1.61 | 0.67 (0.59 to 0.72) |
| Cascade, 40% of the pairs to the model | 0.55 | 0.59 | 1.67 | 0.60 (0.53 to 0.65) |
| Layer only, no model call | 0.42 | 0.52 | 1.76 | 0.42 (0.36 to 0.49) |

The layers add about 0.05 to 0.07 to the raw model, which is within the intervals; the layer without a model call is clearly worse. No variant reaches the shown precision of 0.65 that the earlier decision rule required, so no winner is named by that rule. The full tables per policy are in [data/reports/model_a_comparison.md](data/reports/model_a_comparison.md); the list of requirements to clarify in [data/reports/policy_clarifications.md](data/reports/policy_clarifications.md).

## Running

Reproduction commands are in section 12 of EXPERIMENTS.md. Code follows the style rules checked by `python -m pycodestyle --max-line-length=88 src scripts tests`, `python -m pyright` and `python rules_check.py interview_projects/security_agent` from the repository root; tests run with `python -m pytest`.

