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

Before any design is reviewed, the policy itself is analysed once. The result is a verdict on every requirement of the policy: is it worded clearly enough to be checked, and is there another requirement that contradicts it. These verdicts go to the policy owner as a list of rules to rewrite ([data/reports/policy_clarifications.md](data/reports/policy_clarifications.md)); they do not change the verdicts on the designs, because a design is judged by what it says, also against a vague rule (see "What a verdict means").

1. **The list of requirements.** One model call splits the policy into numbered requirement sentences and gives each its topics (access, logging, payments and so on). Every verdict on a design is given for one of these sentences.
2. **Is the requirement clear?** For every requirement one call asks whether the sentence itself names the measure a design has to meet: a number, a named mechanism or a named standard. The answer is not read from the text but as the probability of "no" from the token log-probabilities, so it can be thresholded. A second call has to copy the general word of degree ("appropriate", "regularly", "long enough") from the sentence. The requirement is called `vague` only when both calls agree, so the model cannot call a rule vague without pointing at the word that makes it vague. "Should" and "shall" are rewritten as "must" before the call.
3. **Does another requirement contradict it?** Comparing every pair of requirements would be slow and would produce many false alarms, so only requirements that are among each other's three nearest neighbours by embedding similarity are compared. For each such pair the model answers three yes/no questions: does B allow less than A, does A allow less than B, and do they set different demands for the same obligation. If the mean probability of "yes" is above a threshold, both requirements are called `contradictory`, and each names the other.

The two thresholds are chosen by two numbers, not by accuracy: the recall of the contradictory sentences and the total of false alarms (clear requirements called vague or contradictory), with at most four false alarms per policy on the training policies v1 to v3 (`pair_threshold` 0.63, `vagueness_threshold` 0.1). On the 140 requirements of the first five policies (v6 and v7 were judged afterwards with the thresholds unchanged): contradictory 13 of 14 found; vague 8 of 20 found; clear called vague 2 and called contradictory 11, of 106 clear (2.6 per policy). On v6 3 of 4 contradictory sentences were found with 1 false alarm; on v7 both contradictory sentences and the one vague rule were found, but one vague and two clear rules were called contradictory. The pair thresholds rest on 7 contradictory pairs in the policies and a bank of 45 pairs written by the same LLM, so they are weakly supported (EXPERIMENTS.md 10p).

## Results: five policies, each left out in turn

Four configurations of the verdict call were run on all five policy groups (`v1 to v3`, `v4`, `v5`, `v6`, `v7`; 210 designs). In all four the model gets one requirement and the 10 design sentences retrieved for it, and answers with a quote, a reason and a verdict; they differ in how long the model reasons before the verdict and in whether it also sees an overview of the service:

| Configuration | Before the verdict | Besides the 10 retrieved sentences | Prompt tokens per document |
|---|---|---|---|
| A | a short reason, at most 25 words | nothing | 14,000 |
| B | a short reason, at most 25 words | the first 800 characters of the design, as an overview of the service | 16,700 |
| C | step-by-step reasoning, at most 60 words | nothing | 14,400 |
| D | step-by-step reasoning, at most 60 words | the overview | 17,100 |

The overview is meant to tell the model what kind of service it is (external or internal, which data it handles), which the retrieved sentences alone may not show; the reasoning is meant to make the model check the requirement against the quote before it commits to a verdict. For each group in turn the decision layer is trained on the other four groups and applied to that group, so no design is scored by a layer that saw its policy. The main number is the recall of the shown requirements (`violated` or `unclear`) when the reviewer accepts 2 false alarms per document: the requirements are ordered by the score of being shown and cut where the false alarms reach 2 per document. It is computed for each policy and averaged over the five policies; the 95% interval resamples the documents of every policy.

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

## Other experiments

The experiments below were run on an earlier version of the data, before the verdict definitions and the designs were revised (EXPERIMENTS.md 10o), so their absolute numbers cannot be compared with the tables above; the comparisons inside each experiment still hold. Each item names the section of [EXPERIMENTS.md](EXPERIMENTS.md) with the full tables.

- **Several requirements in one call** (10i, 10k). The requirements of a policy were grouped by their predicted topic and 1, 2, 4 or 8 of them were judged in one call. On dev, 4 per call cut the calls by four and the prompt tokens by two thirds (42,400 to 14,100 per document) with the same tolerant accuracy (0.748 and 0.752); the quotes suffer first (right verdicts with a quote confirmed in the design fall from 0.60 to 0.56, and to 0.53 at 8 per call). On v4, 2 per call match 1 per call, 4 lose about two points and 8 about five. The time falls little, because generating the answers, not reading the prompt, takes most of it.
- **Size of the context** (10i, 10k). The top 10 and top 20 retrieved sentences against the whole design in every call, on designs of about 700, 3,500 and 10,000 words. The quality of the three is equal within the noise at every length; what differs is the cost: the whole document needs 1.5 times the prompt tokens at 700 words, six times at 3,500 words, and does not fit into the 12,000-token window at 10,000 words, while the top 10 sentences keep the same quality and a flat cost as the design grows.
- **Cost** (10i, 10k, 10q, [data/reports/group_comparison.md](data/reports/group_comparison.md)). Measured on one 8 GB GPU with Qwen3-4B-AWQ on vLLM, calls one after another. On dev (38 requirements per document on average) a document costs 33,000 to 41,000 prompt tokens, 2,300 to 3,500 generated tokens and 44 to 65 seconds; reasoning costs 15 to 20 seconds more than a short reason. The cost grows with the number of requirements, not with the length of the design. A separate verifier call that rechecked every verdict doubled the calls and gave nothing, so it was dropped. On the current data configuration A costs 14,000 prompt tokens per document against 17,100 for D, which decided the choice between variants of equal quality.
- **Cascade** (10i, 10k, 10q). A decision layer that sees only features available before any model call (word overlap, length, topics) decides alone where it is confident, and only the 40% of the pairs where it is least sure go to the model. On the earlier dev data this matched the accuracy of calling the model for every pair (0.794 against 0.798) at 40% of the cost; on the current data it costs 5,600 prompt tokens per document instead of 14,000 but is 0.05 to 0.08 below the full layer (A: recall 0.56 against 0.61 at 2 false alarms per document).
- **Architecture card** (10k). One extra call per design extracts a card of the service (components, data flows, exposure) that replaces the overview. The model gets the exposure of internal services wrong in most cases, and the card does not improve the verdicts beyond the noise.

## Running

The model is served by `scripts/vllm_serve.sh <model> <port>`: vLLM with a context window of 12,288 tokens (the whole-document runs need it), at most 86% of the GPU memory and at most two requests decoded at a time. Whatever the 4-bit weights and activations leave of that share is preallocated as KV cache. Prompts that start with the same fixed instructions reuse the cached prefix, which is why the verifier call, whose answer is two words, added only about ten seconds per document.

Reproduction commands are in section 12 of EXPERIMENTS.md. Code follows the style rules checked by `python -m pycodestyle --max-line-length=88 src scripts tests`, `python -m pyright` (strict) and the AST checker [tools/rules_check.py](tools/rules_check.py), run on each code folder (`python tools/rules_check.py src`, then `scripts` and `tests`): at most 10 statements per function, no magic numbers outside the settings files, type hints on containers, no abbreviations or single-letter names, ordered imports, docstrings. Tests run with `python -m pytest`.

