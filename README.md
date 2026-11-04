# Security Review Agent

Proof of concept of an LLM security design review. Given a company security policy and a software design document, the system gives a verdict on every policy requirement (`compliant`, `violated`, `unclear`, `not_applicable`), quotes the design sentence that decides it, and reports what the author of the design should look at. It runs on a local Qwen3-4B-AWQ model (vLLM, 8 GB GPU) and is evaluated on synthetic designs with exact gold labels.

Layout: `src/secreview` (pipeline), `data` (synthetic cases, policies, ground truth, stored runs), `configs`, `scripts`, `tests`. [EXPERIMENTS.md](EXPERIMENTS.md) records every experiment with its numbers.

## Data

A fictional fintech (14 services). Seven policy documents: three versions of a general policy with 44 rules (`v1` to `v3`, the dev set), and four more policies written after the evaluated variants were fixed: `v4` (15 rules, payments, tenancy, uploads, mobile, incident response, third parties, recovery), `v5` (13 rules, privacy, data residency, change, pipeline, observability, capacity), `v6` (14 rules, architecture review, vulnerability handling, testing, notifications, exports, invoices, fraud, monitoring, webhooks) and `v7` (12 rules, reconciliation, idempotency, limits, API versions, sandbox, messaging, scheduled jobs, support). Every design is judged against the policy it was written for.

| Set | Documents | Pairs scored | Use |
|---|---|---|---|
| dev | 96 designs, policies v1 to v3 | 3549 | development |
| v4 | 24 designs, policy v4 | 384 | the first unseen policy, deliberately different: 43% `not_applicable` |
| v5 | 30 designs, policy v5 | 411 | the second unseen policy |
| v6 | 30 designs, policy v6 | 480 | a third policy, written with the `not_applicable` share of dev |
| v7 | 30 designs, policy v7 | 390 | a fourth policy, the same |
| test | 36 designs of two held-out services | | not used |

**What a verdict means.** The wording of a rule and the verdict are separate. The verdict depends on what the design says: a concrete value or mechanism that the strictest reasonable reading of the requirement accepts is `compliant` (also for a loosely worded rule); silence or a general statement is `unclear`; a decision that breaks even the most lenient reasonable reading is `violated`; a decision that breaks only the strict reading is `unclear`. A service that evidently has no external callers has no external-caller requirement (`not_applicable`). "Should" is read as "must". Rules that leave their measure to the reader (`vague`) or that another sentence relaxes (`contradictory`) are listed separately as requirements for the policy owner to clarify (`scripts/list_policy_clarifications.py`). Gold proportions: dev compliant 60.8%, unclear 16.6%, not applicable 18.4%, violated 4.3%; v4 29.2 / 19.8 / 43.2 / 7.8; v5 49.4 / 22.1 / 17.5 / 10.9; v6 51.7 / 21.0 / 16.3 / 11.0; v7 46.9 / 24.6 / 14.9 / 13.6 (compliant / unclear / not applicable / violated, %). v5 to v7 match dev in the share of `not_applicable` but have two to three times as many violations; v4 is kept as the case of a different mix.

## Pipeline

1. **Policy analysis.** One model call per policy turns the policy into numbered requirement sentences with topics; the wording class (clear, vague, contradictory) is judged afterwards (next section).
2. **Retrieval.** For each requirement the design sentences are ranked with Qwen3-Embedding-0.6B; the 10 best (one sentence per chunk), plus optionally the first 800 characters as a service overview, go into the prompt.
3. **Verdict.** One call per requirement, with a JSON-schema-constrained answer: quote, reasoning of up to 60 words, verdict, severity. The quote is checked against the design text; the probability of the chosen verdict comes from the token log-probabilities.
4. **Decision layer (optional).** A class-weighted logistic regression over the signals of the model and the properties of the requirement, evaluated with cross-validation over services, or trained on one set and applied to another.
5. **Evaluation.** The headline scores are about what the reviewer sees: a requirement is *shown* when the verdict is `violated` or `unclear`; recall, precision and false alarms of showing, a tolerant accuracy, per-class scores and bootstrap intervals over documents.

## Analysis of the policy

One model call lists the requirements of a policy with their topics. A call per requirement judges whether the sentence names its own measure (probability of "no" from the token log-probabilities; "should" and "shall" are read as "must"; a general word of degree has to be copied from the sentence). Requirements that are among the three nearest neighbours in the embedding space are asked three yes/no questions (does B allow less than A, does A allow less than B, do they set different demands for the same obligation); the mean of the three probabilities decides.

The two thresholds are chosen by two numbers, not by accuracy: the recall of the contradictory sentences and the total of false alarms (clear requirements called vague or contradictory), with at most four false alarms per policy on the training policies v1 to v3 (`pair_threshold` 0.63, `vagueness_threshold` 0.1). On the 140 requirements of the first five policies (v6 and v7 were judged afterwards with the thresholds unchanged): contradictory 13 of 14 found; vague 8 of 20 found; clear called vague 2 and called contradictory 11, of 106 clear (2.6 per policy). On v6 3 of 4 contradictory sentences were found with 1 false alarm; on v7 both contradictory sentences and the one vague rule were found, but one vague and two clear rules were called contradictory. The pair thresholds rest on 7 contradictory pairs in the policies and a bank of 45 pairs written by the same LLM, so they are weakly supported (EXPERIMENTS.md 10p).

## Results: five policies, each left out in turn

Four configurations of the verdict call (A short reason, B overview of the service, C reasoning, D reasoning and overview) were run on all five policy groups (`v1 to v3`, `v4`, `v5`, `v6`, `v7`; 210 designs). For each group in turn the decision layer is trained on the other four groups and applied to that group, so no design is scored by a layer that saw its policy. The main number is the recall of the shown requirements (`violated` or `unclear`) when the reviewer accepts 2 false alarms per document: the requirements are ordered by the score of being shown and cut where the false alarms reach 2 per document. It is computed for each policy and averaged over the five policies; the 95% interval resamples the documents of every policy.

| Variant | Mean over 5 policies (95% interval) | v1 to v3 | v4 | v5 | v6 | v7 |
|---|---|---|---|---|---|---|
| A raw | 0.53 (0.47 to 0.58) | 0.31 | 0.58 | 0.65 | 0.44 | 0.69 |
| A + layer, no wording class | 0.61 (0.57 to 0.66) | 0.27 | 0.65 | 0.75 | 0.59 | 0.79 |
| A + layer, wording class per requirement | 0.62 (0.57 to 0.65) | 0.22 | 0.64 | 0.73 | 0.65 | 0.85 |
| C + layer, no wording class | 0.64 (0.60 to 0.69) | 0.34 | 0.67 | 0.80 | 0.63 | 0.78 |
| C + layer, wording class per requirement | 0.65 (0.59 to 0.68) | 0.26 | 0.69 | 0.82 | 0.66 | 0.85 |
| D + layer, no wording class | 0.62 (0.57 to 0.66) | 0.29 | 0.72 | 0.66 | 0.58 | 0.85 |
| D cascade, 40% of the pairs to the model | 0.54 (0.50 to 0.59) | 0.24 | 0.63 | 0.45 | 0.57 | 0.83 |
| Layer only, no model call | 0.44 (0.38 to 0.50) | 0.14 | 0.45 | 0.34 | 0.56 | 0.70 |

All 15 variants, the own decisions of each variant (recall, precision, false alarms per document without a cut), the cost and the paired differences are in [data/reports/group_comparison.md](data/reports/group_comparison.md). Excluding v4 changes no conclusion.

- The layer helps: it raises the raw model on four policies of five (A: +0.07 on v4, +0.10 on v5, +0.15 on v6, +0.10 on v7); the layer without a model call (mean 0.44) is clearly worse than any layer with a model call (0.57 and above).
- On `v1 to v3` the layer does not help (A: 0.31 raw, 0.27 with the layer) and this group has the lowest recall of all. Its shown share is 21% against 32% to 38% in v5 to v7 and its violations are 4% against 11% to 14%; whether this explains the result was not tested.
- The best variants cannot be told apart: C with a layer is first (0.64 and 0.65), A and D with a layer are within 0.02 to 0.03 and the paired intervals contain zero. The raw models are 0.09 to 0.12 below the best; the cascade is 0.07 to 0.09 below.
- The wording class as a feature of the layer changes the mean by 0.01 and lowers the result on v1 to v3 by 0.05 to 0.08; its use is the list of rules to clarify.
- The intervals are about plus or minus 0.03 to 0.05, against plus or minus 0.09 on v4 and v5 alone. The spread of one variant between policies (0.22 to 0.85) is larger than the differences between variants.
- Differences below about 0.04 cannot be separated by these data. By the rule of EXPERIMENTS.md 10p (the best nominal recall, and among the variants not distinguishable from it the cheapest) the choice is A with the layer: 14,000 prompt tokens against 17,000 for D.

The list of rules to clarify is in [data/reports/policy_clarifications.md](data/reports/policy_clarifications.md).

## Running

Reproduction commands are in section 12 of EXPERIMENTS.md. Code is checked with `python -m pycodestyle --max-line-length=88 src scripts tests` and `python -m pyright` (strict); tests run with `python -m pytest`.

