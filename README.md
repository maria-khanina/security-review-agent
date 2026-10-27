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

One model call lists the requirements of a policy with their topics. A call per requirement judges whether the sentence names its own measure (probability of "no" from the token log-probabilities; "should" and "shall" are read as "must"; a general word of degree has to be copied from the sentence). Requirements that are among the three nearest neighbours in the embedding space are asked three yes/no questions (does B allow less than A, does A allow less than B, do they set different demands for the same obligation); the mean of the three probabilities decides.

The two thresholds are chosen by two numbers, not by accuracy: the recall of the contradictory sentences and the total of false alarms (clear requirements called vague or contradictory), with at most four false alarms per policy on the training policies v1 to v3 (`pair_threshold` 0.63, `vagueness_threshold` 0.1). On the 140 requirements of the five policies: contradictory 13 of 14 found; vague 8 of 20 found; clear called vague 2 and called contradictory 11, of 106 clear (2.6 per policy). The pair thresholds rest on 7 contradictory pairs in the policies and a bank of 45 pairs written by the same LLM, so they are weakly supported (EXPERIMENTS.md 10p).

## Results on the unseen policies v4 and v5 (54 designs)

The configurations A (short reason, no overview), B (overview), C (reasoning, no overview) and D (reasoning and overview) were all run again on the redefined gold. Layers are trained on dev only. The main number is the recall of the shown requirements when the reviewer accepts 2 false alarms per document (the requirements are ordered by the score of being shown and cut where the false alarms reach 2 per document), with the 95% bootstrap interval over documents. "Own decisions" are the classes that the variant itself chose, without a cut.

| Variant | Recall at 2 false alarms per document | v4 | v5 | Own decisions: recall / precision / false alarms per document |
|---|---|---|---|---|
| A raw | 0.61 (0.49 to 0.69) | 0.58 | 0.65 | 0.67 / 0.55 / 2.48 |
| A + layer, no wording class | 0.66 (0.58 to 0.74) | 0.58 | 0.75 | 0.62 / 0.64 / 1.56 |
| A + layer, wording class per requirement | 0.68 (0.60 to 0.74) | 0.58 | 0.75 | 0.62 / 0.66 / 1.44 |
| C + layer, no wording class | 0.68 (0.61 to 0.76) | 0.60 | 0.75 | 0.65 / 0.62 / 1.76 |
| D + layer, no wording class | 0.67 (0.58 to 0.72) | 0.62 | 0.69 | 0.62 / 0.63 / 1.61 |
| B + layer, no wording class | 0.61 (0.55 to 0.67) | 0.63 | 0.59 | 0.54 / 0.64 / 1.35 |
| D cascade, 40% of the pairs to the model | 0.61 (0.54 to 0.66) | 0.67 | 0.55 | 0.57 / 0.61 / 1.65 |
| Layer only, no model call | 0.42 (0.36 to 0.50) | 0.49 | 0.32 | 0.42 / 0.52 / 1.76 |

All 15 variants, the recall at 0.5, 1, 2 and 3 false alarms, the cost and the paired differences are in [data/reports/model_comparison.md](data/reports/model_comparison.md).

- A, C and D with a layer are one group: their paired differences are below 0.02 and the intervals contain zero. The layer raises the raw model by 0.05 to 0.15 and removes about one false alarm per document at the model's own decisions; the layer without any model call is clearly worse.
- The wording class as a feature of the layer changes nothing (differences within 0.01). Its use is the list of rules to clarify.
- v4 and v5 give different winners (the cascade is first on v4 and the A and C layers on v5) and the intervals are about plus or minus 0.07: 24 and 30 designs with 106 and 136 shown requirements are too few, and two policies cannot show how much a new policy changes the result. EXPERIMENTS.md 10p explains this and what data would settle it.
- Cheapest variant not distinguishable from the best on the pooled set: the cascade D (6,800 prompt tokens against 14,000), but it is significantly worse on v5, so it is not recommended.

The list of rules to clarify is in [data/reports/policy_clarifications.md](data/reports/policy_clarifications.md).

## Running

Reproduction commands are in section 12 of EXPERIMENTS.md. Code follows the style rules checked by `python -m pycodestyle --max-line-length=88 src scripts tests`, `python -m pyright` and `python rules_check.py interview_projects/security_agent` from the repository root; tests run with `python -m pytest`.

