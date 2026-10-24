# security_agent

Proof of concept of an LLM security design review. Given a company security policy and a software design document, the system gives a verdict on every policy requirement (`compliant`, `violated`, `unclear`, `not_applicable`), quotes the design sentence that decides it, and reports the planted violations and ambiguities. It runs on a local Qwen3-4B-AWQ model (vLLM, 8 GB GPU) and is evaluated on a synthetic dataset with exact gold labels.

Layout: `src/secreview` (pipeline), `data` (synthetic cases, policies, ground truth, stored runs), `configs`, `scripts`, `tests`. [EXPERIMENTS.md](EXPERIMENTS.md) records every experiment with its numbers.

## Data

132 synthetic design documents of a fictional fintech (14 services, 44 policy rules, three policy versions). Every document was authored with planted violations and ambiguities and with statements that satisfy required rules; markers in the authored text give the gold character spans. 96 documents form the dev split and 36 documents of unseen services the test split, which has not been used.

## Pipeline

1. **Policy analysis.** One LLM call per policy version turns the policy into numbered requirement sentences (all 110 gold sentences are found).
2. **Retrieval.** For each requirement the design sentences are ranked with Qwen3-Embedding-0.6B; the 10 best, plus the first 800 characters of the design as a service overview, are shown to the model.
3. **Verdict.** One call per requirement with a JSON-schema-constrained answer: quote, reasoning of up to 60 words, verdict, severity. The quote is checked against the design text; confidence is the probability of the chosen verdict read from the token log-probabilities.
4. **Verifier and decision layer (optional).** A yes/no call per verdict and a class-weighted logistic regression over the verdict probabilities, the verifier, the wording and topics of the requirement and the word overlap with the shown fragments, evaluated with cross-validation over services.
5. **Evaluation.** Gold verdicts for every (document, requirement sentence) pair come from the generator; the headline scores are recall, precision and false alarms of showing a verdict to the user and a tolerant accuracy, with recall and precision per verdict, the AUROC of the confidence and bootstrap intervals over documents for diagnosis.

## Results on the dev split (96 documents, 2998 scored pairs)

A verdict is shown to the user when it is `violated` or `unclear`; `compliant` and `not_applicable` are dropped, so the headline scores are about showing or dropping. Recall is the share of requirements that should be shown which are shown; the false alarm rate is the share of requirements that should be dropped which are shown.

| | Recall | Precision | False alarms per document | Tolerant accuracy |
|---|---|---|---|---|
| per-requirement, model verdicts (short reason) | 0.26 | 0.72 | 1.1 | 0.701 |
| per-requirement, model verdicts (reasoning before the verdict) | 0.53 | 0.65 | 3.1 | 0.729 |
| + verifier + decision layer | 0.69 | 0.77 | 2.3 | 0.815 |

On the 30 pilot documents the free-form single-call reviewer shows 3% of the requirements that should be shown. The limit of the per-requirement review is the 4B model: it recognises only about 60% of the planted violations as violations. The decision layer fixes the leniency of the model, but its gain comes partly from priors of this policy (topics, wording of the requirement), see EXPERIMENTS.md sections 10d to 10f; it has not been tested on a new policy.

Cost per document of the best configuration, measured on three documents with an otherwise idle server: 79 model calls (39 verdicts and 40 verifier calls), about 54,000 prompt tokens, 3,600 generated tokens and 68 seconds when the calls run one after another.

## Running

Reproduction commands are in section 12 of EXPERIMENTS.md. Code follows the style rules checked by `python -m pycodestyle --max-line-length=88 src scripts tests`, `python -m pyright` and `python rules_check.py interview_projects/security_agent` from the repository root; tests run with `python -m pytest`.
