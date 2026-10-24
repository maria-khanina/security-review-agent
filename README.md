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
5. **Evaluation.** Gold verdicts for every (document, requirement sentence) pair come from the generator; scores are accuracy, recall and precision per verdict, defect recall (planted violations with the right quote and planted ambiguities), confidence AUROC, with bootstrap intervals over documents.

## Results on the dev split (96 documents, 3583 pairs)

| | Accuracy | Defect recall | Violated quotes hitting a planted violation (P / R) |
|---|---|---|---|
| free-form single call (30-document pilot) | | 0.16 | |
| per-requirement, model verdicts (reasoning prompt) | 0.58 | 0.60 | 0.59 / 0.64 |
| per-requirement + verifier + decision layer | 0.76 to 0.77 | 0.50 | 0.67 / 0.66 |

On the same 30 pilot documents the per-requirement review finds 2 to 3 times as many planted violations and 5 to 14 times as many planted ambiguities as the free-form review, at the same precision of `violated`. The limit is the 4B model: about 40% of the planted violations are not recognised. The decision layer fixes the leniency of the model (accuracy +18 to +25 points) but its gain comes mostly from priors of the requirement (topics, wording), see EXPERIMENTS.md section 10d.

## Running

Reproduction commands are in section 12 of EXPERIMENTS.md. Code follows the style rules checked by `python -m pycodestyle --max-line-length=88 src scripts tests`, `python -m pyright` and `python rules_check.py interview_projects/security_agent` from the repository root; tests run with `python -m pytest`.
