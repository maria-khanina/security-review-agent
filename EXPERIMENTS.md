# Experiment log

This log describes every experiment run so far on the security design review prototype, what each variant does, and the numbers it produced. It is written to be read without any other context.

The task: given a company security policy and a software design document, report the places where the design violates a policy requirement (`violation`) or is too vague or silent for a requirement to be judged (`ambiguity`). Everything is measured on synthetic data (section 1). All numbers are on the **dev** split (96 documents). The **test** split (36 documents) has not been opened. Intervals are 95% bootstrap intervals over documents (2000 resamples; "paired" means two variants are compared on the same resamples).

## 0. Terms and metrics

- **Gold item**: a planted flaw or a planted compliant statement with its exact character span in the design text, written by the data generator.
- **Finding**: one reviewer output: a quoted design sentence, the policy requirement it concerns, a type (`violation` or `ambiguity`), a severity (`low`, `medium`, `high`, `critical`) and a confidence (1 to 100).
- **Match**: a finding matches a gold flaw when the token overlap (intersection over union, IoU) of their design spans is at least 0.3, one finding per gold flaw. **Loose** matching looks at the design span only. **Strict** matching also requires that the cited policy sentence overlaps the gold policy span.
- **Recall of all flaws**: matched gold flaws divided by all gold violations and ambiguities of the evaluated documents. **Recall of important flaws**: the same restricted to gold flaws of severity `high` or `critical`.
- **Precision**: matched findings divided by all findings. **False alarms per document**: unmatched findings divided by the number of documents.
- **Policy status** of a rule in a given policy version: `clear` (concrete, checkable), `vague` (relies on words like "appropriate"), `advisory` ("should", "may"), `conflicting` (another policy sentence allows less).

## 1. Dataset

- 132 synthetic design documents for a fictional fintech, Meridian Pay: 14 documented services, 44 atomic policy rules, three policy versions (v1 an "Information Security Policy" of about 5100 characters, v2 "Security Standards" of about 5500, v3 an "Engineering Security Handbook" of about 2700 with MUST/SHOULD wording). 48, 49 and 35 documents use v1, v2 and v3.
- Each document was authored from a brief with planted flaws and with statements that satisfy required rules. Authors differ in style (bullet lists, long prose, migration deltas, merged documents, notes); documents have light typos and markdown irregularities. Markers `⟦ID|text⟧` in the authored text give the gold character spans.
- Splits: dev 96 documents, test 36 documents of services not seen in dev. Dev gold: 76 violations, 68 ambiguities (both in scope), 61 drift flaws (design versus implementation, out of scope), 25 documents without any flaw. Policy status of the in-scope dev flaws: 93 clear, 23 vague, 21 advisory, 7 conflicting.
- 1791 satisfied statements in total (1322 in dev): a design sentence that fulfils a required rule, labelled with the rule.
- Each gold ambiguity points at one design sentence, but that sentence is an anchor (where the missing statement should have been), not evidence (section 7).

## 2. The baseline reviewer (common to all variants)

- **Input**: one LLM call per document. The policy text is given as reference material in which every requirement sentence carries a tag `[R12]`; then the design text.
- **Model**: Qwen3-4B-AWQ on a local vLLM server, temperature 0, at most 4000 output tokens, thinking mode off. The reply is constrained by a JSON schema (vLLM `response_format`), including an enumeration of the allowed requirement ids.
- **Prompt ideas shared by all variants**: the role is a senior application security engineer; the policy is reference material, not a checklist to walk through; report every problem found, no cap on their number; two finding kinds, `violation` (the design states a decision that breaks a requirement) and `ambiguity` (the design is vague or silent about something a requirement needs; the author must clarify, no guessing); an explicit four-level severity scale (critical: secrets, card numbers or personal data reachable directly by outsiders with no other weakness; high: serious exposure that needs one more condition; medium: weak defence in depth, non-sensitive data or internal component; low: hygiene or documentation gap), an ambiguity is rated one level below the violation it could hide; an explicit 1 to 100 confidence scale (how likely a careful reviewer would confirm: 90 to 100 no alternative reading, 70 to 89 very likely, 50 to 69 plausible, 30 to 49 weak signal, below 30 speculation) with an instruction to use the whole scale; five rules (the design quote is copied character for character, one or two sentences; the requirement id is a tag that appears in the policy; the observation is at most 25 words; report only what the two texts show; return an empty list if there is nothing). No few-shot examples.
- **Output fields in this order**: `design_quote`, [`topics`], `observation`, `requirement_id`, `finding_type`, `severity`, `confidence`.
- **Code around the model** (not left to the model): the requirement ids come from a numbered policy analysis built once per policy version (section 3), not from the model; a quote that cannot be found in the design (fuzzy similarity of at least 90, at least 12 characters) is rejected as a hallucination and counted; a second finding with the same requirement id whose design quote overlaps an earlier one (IoU at least 0.3) is dropped as a duplicate; a truncated reply is repaired by recovering the complete findings before the cut; the recommended action is derived in code (`review_policy` if the cited requirement is not clear, `clarify` for an ambiguity, `fix` otherwise).

## 3. Policy analysis: turning the policy into numbered requirements

The reviewer cites requirement tags, so the policy is first split into requirement sentences. One LLM call per policy version returns, for each requirement sentence, a quote and metadata; code finds each quote in the policy text (fuzzy match, at least 90), drops quotes that cannot be found, numbers the rest R1, R2 in text order and takes the quote text from the policy itself. The gold ("oracle") list has 110 requirement sentences over the three versions: 72 clear, 28 vague or advisory, 10 contradictory (sentences that conflict with another sentence). Three prompts were compared; the stored sets are `data/policy_analysis/llm_analysis_v1`, `_v2`, `_v3`.

- **Prompt 1** asks the model to copy each requirement and to classify its wording directly as `clear` (a concrete, checkable obligation), `vague_or_advisory` (general words such as "appropriate", or only advisory "should"/"may") or `contradictory` (another statement conflicts with it; list both statements), plus one to three topics from a fixed list of twelve.
- **Prompt 2** keeps the format but sharpens the criteria: `clear` needs a concrete criterion (a number, a named algorithm, protocol or system, or a precise prohibition), "must" alone is not enough; it lists trigger words for vague wording and tells the model to scan the whole policy for relaxing words ("may", "up to", "until", "unless", "except", "acceptable") and then mark both the rule and the relaxing sentence contradictory; topics are limited to the one or two the sentence itself mentions.
- **Prompt 3** takes the decision away from the model: for each requirement it returns the quote, the exact `loose_phrases` that make it general, the sentence `relaxed_by` that allows less, and topics. Code decides: a requirement is `vague_or_advisory` when at least one loose phrase occurs verbatim in the quote, and a requirement and its verified `relaxed_by` sentence are both `contradictory`.

Results on the 110 gold requirements (all three policy versions together):

| | Prompt 1 | Prompt 2 | Prompt 3 |
|---|---|---|---|
| Requirement sentences found (recall) | 110 of 110 | 110 of 110 | 110 of 110 |
| Predicted sentences / precision | 112 / 0.982 | 112 / 0.982 | 112 / 0.982 |
| Wording accuracy (always answering "clear" gives 0.655) | 0.745 | 0.745 | 0.409 |
| Recall of `clear` sentences | 1.000 | 1.000 | 0.264 |
| Recall of `vague_or_advisory` (28) | 0.357 | 0.357 | 0.929 |
| Recall of `contradictory` (10) | 0.000 | 0.000 | 0.000 |
| Recall / precision of "not clear" (38) | 0.368 / 1.000 | 0.395 / 1.000 | 0.868 / 0.384 |
| Topics: share with at least one correct topic / Jaccard | 0.882 / 0.603 | 0.936 / 0.609 | 0.855 / 0.567 |

- Finding the requirement sentences is solved. Classifying their wording is not: prompts 1 and 2 almost never call anything vague (18 of 28 vague sentences are called clear) and never find a contradiction; they are right when they do call something vague (precision 1.0).
- Prompt 2 moved one contradictory sentence to "vague" compared with prompt 1 and improved topics; the wording accuracy is unchanged.
- Prompt 3 overshoots: the verbatim loose phrases occur in 53 of 72 clear sentences, so these are called vague, and precision of "not clear" falls to 0.384. It was shelved.
- The pilot of section 4 used the analysis from prompt 1. The oracle list (gold requirements) is also available to isolate later stages.

## 4. Baseline reviewer pilot on 30 dev documents (data before section 6)

The 30 documents are fixed (`configs/dev_pilot.yaml`, stratified by service); gold: 35 scorable flaws (17 ambiguities, 18 violations), 8 of high or critical severity, plus 13 out-of-scope drift flaws. All four runs use the same policy analysis (prompt 1) and differ only in the prompt:

1. **plain**: the prompt of section 2 without the topics field.
2. **topics**: the output has a `topics` field first. The model names the security topics (one to three of twelve) of the quoted sentence before choosing the requirement, which must then share a topic.
3. **topics + compliant**: additionally a third finding type `compliant` is allowed. The prompt says that a design sentence that states what a requirement demands is not a problem and should be reported as `compliant`. These entries are discarded in code.
4. **topics + compliant + silence**: additionally an instruction to report an ambiguity, quoting the sentence that names the component, when the design describes a component and a requirement clearly concerns it but the design says nothing.

| Run | Findings | Matched flaws | Precision | False alarms / doc | Recall, all flaws | Recall, important (8) | Violation recall (of 18) | Ambiguity recall (of 17) |
|---|---|---|---|---|---|---|---|---|
| plain | 262 | 12 | 0.046 | 8.33 | 0.343 | 0.375 | 9 | 3 |
| topics | 246 | 16 | 0.065 | 7.73 | 0.457 | 0.625 | 13 | 3 |
| topics + compliant | 43 | 12 | 0.279 | 1.03 | 0.343 | 0.625 | 9 | 3 |
| topics + compliant + silence | 67 | 13 | 0.194 | 1.80 | 0.371 | 0.500 | 10 | 3 |

- The topics field raised matched flaws from 12 to 16 and recall of important flaws from 0.375 to 0.625, with almost no change in precision.
- The `compliant` option removed 203 of 246 findings (false alarms per document from 7.73 to 1.03, precision 0.065 to 0.279) at equal recall of important flaws, but it also cost 4 matched violations (13 to 9): some real violations were relabelled compliant. This is the best precision so far; recall of all flaws is 0.343.
- The silence instruction lowered both precision and recall of important flaws, and did not find more ambiguities.
- Ambiguity recall is 3 of 17 in all four runs.
- Of the 12 matched findings in the best run, the cited policy sentence was right in half (policy evidence accuracy 0.5); the `review_policy` action had recall 0 (3 of 3 such flaws received `fix`) because the policy analysis does not detect vague sentences (section 3).
- Severity of matched findings was exact in 5 of 12 (accuracy 0.42); the ordinal error is reported in `data/runs/*/metrics_dev.json`.
- Verbalized confidence separates correct from wrong findings weakly (AUROC 0.63 on an earlier run).
- Limits: 30 documents, intervals are wide, four runs were compared on the same documents (multiple comparisons).

## 5. Retrieval of design fragments for a requirement (no LLM)

Question: given one policy requirement sentence, can we find the design sentence that decides it, so that a later step can judge each requirement from a short context instead of the whole design?

- **Setup**: the design is split into units (sentences or list items). A **chunk** is a unit together with a window of neighbouring units inside the same section: window 0 (the unit alone) or window 1 (one neighbour on each side). The query is the text of the policy sentence. The ranker orders the chunks of one document.
- **Gold pairs on dev**: 1470 pairs of (document, policy sentence): 77 violations, 71 ambiguities, 1322 satisfied statements. The gold design span is the flaw span or the satisfied span.
- **Rankers**: BM25 (lexical, on lower-cased word tokens); dense (cosine similarity of embeddings), with the models bge-large-en-v1.5 (335M parameters, with its query prefix) and Qwen3-Embedding-0.6B (600M, with an instruction prefix describing the task); hybrid (reciprocal rank fusion, constant 60, of the BM25 ranking and the dense ranking); reranker (the cross-encoder bge-reranker-base re-orders the 20 best chunks of a first-stage ranker, the rest keep their order).
- **Metrics**: recall@k = the share of pairs whose gold span overlaps a unit of one of the first k chunks; reciprocal rank = 1 divided by the rank of the first chunk that overlaps the gold span (averaged over pairs); context size = characters of the merged units of the first k chunks; "within a budget" = recall when only as many chunks are taken as fit into the given number of characters.

Recall@k on violations and ambiguities together (148 pairs, window 0; 95% intervals in brackets for Qwen):

| Ranker | @1 | @3 | @5 | @10 | @20 |
|---|---|---|---|---|---|
| BM25 | 0.22 | 0.37 | 0.49 | 0.63 | 0.80 |
| bge-large | 0.31 | 0.49 | 0.56 | 0.74 | 0.90 |
| Qwen3-Embedding-0.6B | 0.40 | 0.55 | 0.61 [0.55, 0.68] | 0.78 | 0.92 |
| Hybrid BM25 + Qwen | 0.33 | 0.48 | 0.57 | 0.75 | 0.95 |
| bge-large + reranker | 0.13 | 0.34 | 0.48 | 0.70 | 0.90 |
| Qwen + reranker | 0.12 | 0.35 | 0.48 | 0.72 | 0.92 |

Qwen and the hybrid by kind (window 0; window 1 adds 0 to 0.06 at @5):

| Kind | Ranker | @1 | @5 | @10 | @20 |
|---|---|---|---|---|---|
| violation (77) | Qwen | 0.66 | 0.90 | 0.96 | 1.00 |
| violation (77) | hybrid | 0.51 | 0.77 | 0.87 | 1.00 |
| ambiguity (71) | Qwen | 0.11 | 0.31 | 0.59 | 0.83 |
| ambiguity (71) | hybrid | 0.14 | 0.35 | 0.62 | 0.90 |

- Qwen3-Embedding-0.6B beats bge-large: recall@1 +0.09 and reciprocal rank +0.08 (paired intervals exclude zero); at @5 the gap +0.05 is within noise (window 1: 0.65 versus 0.60, significant).
- The hybrid has the best recall@20 of all variants (0.95 at window 0, 0.94 at window 1 against 0.87 for Qwen alone at window 1, a significant gain). The gain comes from ambiguities (+0.07 at window 0, +0.13 at window 1); on violations both reach 1.00. At the top ranks the hybrid is worse than Qwen alone on violations (@1 −0.16, @3 −0.13, significant).
- The reranker does not help at any cutoff that matters: recall@5 falls from 0.56 to 0.48 (bge-large) and from 0.61 to 0.48 (Qwen), recall@10 from 0.74 to 0.70 and from 0.78 to 0.72, and recall@20 is unchanged by construction, because it only reorders the first 20 chunks. Recall@1 also falls (0.31 to 0.13 for bge-large). A likely cause is that it puts statements that resemble the requirement first, and violations rarely resemble it. It is dropped.
- Window 1 raises recall@k but costs more text: under a budget of 600 characters it is worse than window 0 (0.43 to 0.51 versus 0.57 to 0.63 for the dense rankers). Adding the section heading to the chunk text made no significant difference.
- Satisfied statements are found almost perfectly by every ranker (recall@5 about 1.0) and cannot be used to choose a retriever.
- Limits: the queries are the true policy sentences; a model-built policy analysis will be worse. The documents are short (section 8): 20 candidates are already about 40% of a document, so recall@20 is optimistic for long documents (not measured).

## 6. Varying the wording of satisfied statements

The authored satisfied statements were near copies of the rule statement (similarity of at least 85 on 1342 of 1791). For each of the 44 rules four alternative wordings were written (`data/policies/compliant_phrasings.yaml`); a deterministic seeded choice replaces the text of a satisfied marker with one of the four wordings or keeps the original (one chance in five), only for statements that are near copies and whole sentences. 814 statements in 120 documents were changed; near copies fell from 1342 to 432. Labels, types and rule ids are identical in all 132 documents; only span positions moved. Retrieval of satisfied statements stayed near 1.0, because the new wordings keep the domain terms (MFA, KMS, 14 days). Paraphrase at sentence level does not make this class hard; statements with system-specific wording would.

## 7. What a retrieval miss costs on ambiguities (LLM probe)

The 71 ambiguity pairs; for each, the local model saw the requirement and the 10 best fragments of Qwen (window 0) and chose a verdict: `compliant`, `violated`, `vague` (about the subject but too general to judge) or `not_addressed` (nothing about the subject).

| Group | Pairs | not_addressed | vague | compliant | violated |
|---|---|---|---|---|---|
| gold sentence in the top 10 | 42 | 21 | 10 | 10 | 1 |
| gold sentence missed | 29 | 15 | 10 | 2 | 2 |
| missed, gold sentence added | 29 | 16 | 10 | 2 | 1 |

- The gold sentence of an ambiguity is an anchor, not evidence. In the 7 misses read by hand the retrieved fragments said nothing about the requirement; the gold sentences were unrelated ("ledger-core exposes the list and search calls over entries by account, date range and reference" for the requirement "use parameterized queries only").
- In 25 of 29 misses the model still concludes `vague` or `not_addressed`, that is, an ambiguity; adding the gold sentence changes almost nothing. What is lost is only the location in the design.
- The boundary between `not_addressed` and `vague` is not defined by the gold labels (one type, `ambiguity`, one action, `clarify`) and the 4B model does not hold it (a fragment about data collection was called `vague` for a requirement about disclosure to third parties). Decision: one verdict for "not enough information" plus free text on what is missing.
- Limits: a 4B model in one pass, my own four-verdict scheme, 7 of 29 misses read by hand.

## 8. Cost of the retrieved context

Mean tokens (Qwen tokenizer) of the merged first k chunks, over the 148 violation and ambiguity pairs; window 0 / window 1:

| Candidates | Qwen | Hybrid |
|---|---|---|
| top 5 | 112 / 167 | 117 / 176 |
| top 10 | 213 / 290 | 225 / 304 |
| top 20 | 394 / 479 | 412 / 501 |

A whole design has 883 tokens on average (maximum 1571); the reviewer system prompt is 699 tokens; the policy is 530 to 1161 tokens. The context window of the vLLM server is 12288 tokens. A call with 20 candidates fits easily (about 2000 to 2500 tokens), but the documents are so short that 20 candidates are already about half of a document, so retrieval saves little here.

## 9. Verdict per requirement: definitions and gold

The next reviewer design asks for one verdict per numbered policy requirement instead of free-form findings. Four verdicts:

- `compliant`: the design states what the requirement demands, and the requirement is worded clearly enough for that statement to count as fulfilment. A quote of the design is required.
- `violated`: the design states a decision that contradicts the requirement. A quote of the design is required.
- `unclear`: the requirement applies to the design but cannot be settled, for one of two reasons. Either the design is silent or too general about it, or the requirement itself is worded vaguely or only as advice, or conflicts with another policy sentence, so that even a clear statement in the design could not be called fulfilment or violation. No quote.
- `not_applicable`: the requirement does not concern the service, or cannot be judged from a design document at all (it concerns only settings of the implementation). No quote.

The gold verdict of every (document, policy requirement sentence) pair is computed from the generator's knowledge (`src/secreview/evaluation/verdict_truth.py`), first matching rule wins:

1. the rule does not apply to any component of the service: `not_applicable` (not in service);
2. the rule is checked only in the implementation (`NET-03`, the only such rule): `not_applicable` (implementation only);
3. a violation is planted on the rule: `violated`, gold quote = its design span;
4. an ambiguity is planted on the rule: `unclear` (planted ambiguity);
5. the design has a statement that satisfies the rule: `compliant`, gold quote = that statement;
6. the policy wording of the rule is vague, advisory or conflicting: `unclear` (vague policy);
7. a drift flaw (design versus implementation, out of scope) carries a design claim about the rule: `compliant`, gold quote = the claim (drift claim);
8. otherwise `unclear` (silence by construction: a planted flaw on a coupled rule made the generator leave the statement out, for example no statement about secrets in code when how secrets are obtained was left vague).

Gold on dev, 3583 pairs (policy requirement sentences, 3441 rules, because some rules have two sentences):

| Verdict | Pairs | Subtypes |
|---|---|---|
| `not_applicable` | 1186 | not in service 1090, implementation only 96 |
| `compliant` | 1353 | stated 1322, drift claim 31 |
| `unclear` | 970 | vague policy 857, planted ambiguity 71, silence by construction 42 |
| `violated` | 74 | planted violation 74 |

`unclear` is more than a quarter of all pairs, mostly vague policy wording, so scores are reported per subtype, and a separate score covers the planted violations and ambiguities ("defect recall"). The four violations without any location in the design are all `NET-03` and have become `not_applicable`.

The scorer (`src/secreview/evaluation/verdict_scores.py`) matches the requirements of a policy analysis to the gold requirement sentences (one to one, token IoU of at least 0.3), compares verdicts and, for `compliant` and `violated`, requires the quoted design span to overlap the gold span (IoU of at least 0.3). It reports a 4 x 5 confusion table (the fifth predicted class is "missing", a gold requirement the analysis did not find), accuracy with and without the quote, recall per subtype, how often a right verdict also has the right quote, defect recall, and the precision of `violated`. Checks without any model: a perfect answer scores 1.0 everywhere; shifting the quotes keeps the verdict accuracy and loses the evidence; dropping half of the requirements shows up as missing pairs; answering `unclear` everywhere is right exactly on the `unclear` share (27%).

An open consequence for the user-facing report: about 8 vague-wording `unclear` verdicts per document (857 pairs in 96 documents) are remarks about the policy, identical for all documents of a policy version; they should be shown once per policy version (action `review_policy`), not in every design review.

## 10. Per-requirement verdict pipeline on the 30-document dev pilot

**Pipeline.** The requirements come from the stored policy analysis `llm_analysis_v2` (prompt 2 of section 3; it finds all 110 gold requirement sentences). For each requirement the design is ranked once on the GPU (Qwen3-Embedding-0.6B, cosine similarity, chunks of one sentence) and the 10 best chunks are shown to the model in document order. One call per requirement to Qwen3-4B-AWQ (temperature 0, JSON schema): the prompt defines the four verdicts of section 9, the severity scale of section 2 and asks for `quote`, `reason` (at most 25 words), `verdict`, `severity` in this order. The quote of `compliant` and `violated` is located in the design text (fuzzy match, at least 90); the severity counts only for `violated`. Confidence is the probability of the chosen verdict among the four, read from the log-probabilities of the first token of the verdict (normalised over the four verdicts). About 38 seconds per document.

**Pilot.** The 30 pilot documents of section 4 give 1151 (document, requirement sentence) pairs scored with section 9: 455 `compliant`, 19 `violated`, 294 `unclear`, 383 `not_applicable`. Reported: accuracy of the verdict, recall / precision per verdict, "defect recall" (planted violations with the right quote plus planted ambiguities), AUROC of the confidence for telling right verdicts from wrong ones. Intervals and paired differences are bootstrap over documents (`scripts/evaluate_verdicts.py`).

| Run | Accuracy | compliant R / P | violated R / P | unclear R / P | not_applicable R / P | Defect recall | Confidence AUROC |
|---|---|---|---|---|---|---|---|
| base: top 10 chunks | 0.528 | 0.98 / 0.55 | 0.84 / 0.42 | 0.27 / 0.44 | 0.17 / 0.56 | 0.57 | 0.81 |
| strict wording of `compliant` and `not_applicable` in the prompt | 0.534 | 0.97 / 0.57 | 0.68 / 0.41 | 0.38 / 0.42 | 0.13 / 0.62 | 0.62 | 0.78 |
| oracle context: gold sentence guaranteed in the 10 chunks | 0.531 | 0.98 / 0.55 | 0.84 / 0.43 | 0.29 / 0.45 | 0.17 / 0.56 | 0.57 | 0.81 |
| first 800 characters of the design added as a service overview | 0.526 | 0.99 / 0.52 | 0.74 / 0.50 | 0.17 / 0.42 | 0.24 / 0.65 | 0.51 | 0.78 |

- **Retrieval is not the bottleneck at 10 candidates.** Guaranteeing the gold sentence in the context changes nothing (accuracy +0.003, paired interval includes 0; violated recall identical): the gold sentence of the evidence verdicts was already among the 10 chunks. The limit is the judgment of the 4B model in one pass.
- **The model is too lenient.** It answers `compliant` for about 70% of the pairs (gold 40%), whenever a fragment is about the same subject, for example "secrets are not in the repository" for a requirement about card numbers. Recall of `compliant` is 0.98 but precision only 0.55; `not_applicable` is found in 17% of the cases and `unclear` in 27%.
- **A stricter prompt moves answers from `compliant` to `unclear`** (recall of `unclear` +0.11, planted ambiguities 0.33 to 0.56, vague policy 0.27 to 0.37; recall of `violated` −0.16) but accuracy does not change (0.528 to 0.534, interval includes 0).
- **The service overview moves answers to `not_applicable`** (recall +0.07, significant, both for exposure-driven and component-driven cases) at the cost of `unclear` (−0.10); accuracy does not change.
- **The gold `not_applicable` is partly an artifact of the generator.** 580 of the 1090 dev pairs that are "not in service" (53%) are not applicable only because each documented service has a single exposure value (external, internal or admin): internal service authentication (`AUTH-02`), encryption of internal traffic (`CRYPTO-04`) and least-privilege roles (`AUTHZ-02`) are marked not applicable for an externally exposed service, although such a service also has internal calls. They are reported as the subtype `not_in_service_exposure`, apart from the component-driven `not_in_service` (a service without card data, buckets or a log pipeline). The model finds 16% and 20% of them respectively.
- **Confidence.** The log-probability confidence separates right from wrong verdicts with AUROC 0.81 (interval 0.78 to 0.84), although it is almost always close to 1.
- **Severity.** Only 15 right `violated` verdicts on the pilot; mean absolute error 0.5 to 0.6 levels. Too few for conclusions; measured again on the full dev split.
- **Comparison with the free-form baseline of section 4** is only indicative, because the scores differ: that baseline found 12 of 35 planted flaws (recall 0.34) with 1.03 false alarms per document; here 57% of the planted violations and ambiguities (defect recall) are found.

**Verifier threshold (first signal).** A second call per `compliant` or `violated` verdict asks a yes/no question suited to the verdict ("does the quoted sentence itself state what the requirement demands?"); the probability of yes is read from the token log-probabilities. Downgrading verdicts to `unclear` when this probability is below a threshold raises accuracy on the pilot from 0.528 to 0.573 (threshold 0.98), precision of `compliant` from 0.55 to 0.65, recall of `unclear` from 0.27 to 0.46 and precision of `violated` from 0.42 to 0.58, at the cost of recall of `violated` (0.84 to 0.74). The threshold was chosen on the same pilot documents, so this is an upper estimate.

### 10.1 Confidence, severity and a decision layer (pilot, overview run)

Starting point: the run with the service overview (first 800 characters of the design added), 1151 pairs, accuracy 0.526, verdict probabilities stored.

- **Three confidences compared by AUROC** (right versus wrong verdicts): probability of the chosen verdict from the log-probabilities 0.78; probability of yes of the yes/no verifier 0.79; the model stating a number from 1 to 100 in a separate call 0.72. Neither extra call beats the free log-probability confidence.
- **Severity in a separate call** for the 14 right `violated` verdicts: mean absolute error 0.64 levels against 0.57 for the severity given in the verdict call (exact 6 of 14 against 7 of 14). No gain.
- **Decision layer.** A class-weighted multinomial logistic regression (`verdict_stacking.py`) combines the log-probabilities of the four verdicts, the verifier probability, whether a quote was found, the wording class of the requirement, the largest word overlap between the requirement and the shown fragments, the overlap with the quote, the length of the requirement and its topics. It is scored with cross-validation over groups of documents (five folds, all documents of one service in the same fold, so no service is seen in training). Results on the pilot:

| Run | Accuracy | compliant R / P | violated R / P | unclear R / P | not_applicable R / P | Defect recall | Macro F1 |
|---|---|---|---|---|---|---|---|
| model verdicts (overview run) | 0.526 | 0.99 / 0.52 | 0.74 / 0.50 | 0.17 / 0.42 | 0.24 / 0.65 | 0.51 | 0.467 |
| + decision layer without topics | 0.702 | 0.95 / 0.88 | 0.68 / 0.50 | 0.34 / 0.50 | 0.69 / 0.60 | 0.43 | 0.635 |
| + decision layer with topics | 0.783 | 0.92 / 0.92 | 0.68 / 0.48 | 0.66 / 0.66 | 0.72 / 0.73 | 0.57 | 0.718 |

- Most of the gain comes from `not_applicable` (recall 0.24 to 0.70) and from the precision of `compliant` (0.52 to 0.88): the layer learns that a verdict `compliant` from a model that is not sure, a requirement of vague wording or a fragment with little word overlap are better answered `unclear` or `not_applicable`. Giving the layer a class weight of one instead of the square root raises recall of `unclear` and `violated` further, at lower precision of `violated` (0.39).
- **Caveat.** The layer is trained on gold verdicts of dev documents, and the topic features carry per-requirement priors of this policy (for example which requirements are mostly vague or inapplicable). With a new policy it has to be retrained on labelled reviews. Cross-validation over services estimates how it transfers to unseen services, which is the situation of the test split.

### 10.2 Reasoning before the verdict (pilot)

The `reason` field is asked to be up to 60 words that come before the verdict: list what the requirement demands (values, mechanism, scope), say for each element whether a fragment states it, and name what is missing (instead of 25 words about what the fragments say). Same overview, same contexts.

| Run | Accuracy | compliant R / P | violated R / P | unclear R / P | not_applicable R / P | Defect recall | Macro F1 |
|---|---|---|---|---|---|---|---|
| overview, short reason | 0.526 | 0.99 / 0.52 | 0.74 / 0.50 | 0.17 / 0.42 | 0.24 / 0.65 | 0.51 | 0.467 |
| overview, reasoning before the verdict | 0.593 | 0.97 / 0.68 | 0.68 / 0.46 | 0.49 / 0.43 | 0.22 / 0.64 | 0.73 | 0.533 |
| ... then decision layer (with verifier) | 0.779 | 0.94 / 0.91 | 0.68 / 0.48 | 0.65 / 0.65 | 0.69 / 0.74 | 0.54 | 0.714 |

The paired differences of the raw verdicts are significant: accuracy +0.067, recall of `unclear` +0.33, defect recall +0.22 (interval 0.05 to 0.39). After the decision layer the two prompts end at the same accuracy (0.78), so the reasoning mainly matters when the verdicts are used without the layer.

### 10.3 Against the free-form reviewer (pilot, defect scores only)

The findings of the free-form reviewer of section 4 can be read as verdicts on requirements: a violation as `violated` with its quote, an ambiguity as `unclear`, the most confident finding per requirement (`scripts/compare_baseline.py`). Only the planted defects are comparable, since that reviewer says nothing about compliant or not applicable requirements.

| Reviewer | Planted violations found | Planted ambiguities found | Defect recall | Violated verdicts given / precision |
|---|---|---|---|---|
| free-form, topics + compliant (best of section 4) | 0.26 | 0.06 | 0.16 | 10 / 0.50 |
| free-form, plain | 0.26 | 0.11 | 0.19 | 105 / 0.05 |
| per-requirement, overview | 0.74 | 0.28 | 0.51 | 28 / 0.50 |
| per-requirement, reasoning before the verdict | 0.63 | 0.83 | 0.73 | 28 / 0.46 |

At the same precision of `violated` the per-requirement review finds about two to three times as many planted violations and five to fourteen times as many planted ambiguities (0.28 and 0.83 against 0.06 to 0.11). The free-form reviewer judges only the places it happens to notice; the per-requirement reviewer is forced to look at every requirement.

## 10b. Full dev split (96 documents, 3583 pairs)

The overview configuration (section 10; reasoning short) was run on all 96 dev documents, then the verifier, then the decision layer with cross-validation over groups of documents of the same service (`dev_overview800`, `dev_overview800_verified`, `dev_overview800_stacked`). Intervals are bootstrap over documents.

| | Model verdicts | With decision layer | Paired difference |
|---|---|---|---|
| Accuracy | 0.510 [0.491, 0.528] | 0.764 [0.750, 0.777] | +0.254 [+0.238, +0.270] |
| Macro F1 | 0.442 | 0.692 | +0.251 |
| `compliant` recall / precision | 0.99 / 0.50 | 0.92 / 0.91 | precision +0.41 |
| `violated` recall / precision | 0.61 / 0.44 | 0.58 / 0.44 | no change |
| `unclear` recall / precision | 0.19 / 0.46 | 0.66 / 0.65 | recall +0.47, precision +0.19 |
| `not_applicable` recall / precision | 0.21 / 0.64 | 0.68 / 0.72 | recall +0.47 |
| Defect recall (planted violations with the right quote and planted ambiguities) | 0.43 [0.35, 0.52] | 0.48 [0.40, 0.57] | +0.05 (interval includes 0) |
| Planted violations / planted ambiguities found | 0.58 / 0.28 | 0.54 / 0.42 | |
| Violated quotes that hit a planted violation of the document, any requirement | precision 0.64, recall 0.68 | precision 0.66, recall 0.65 | |

- The decision layer fixes the leniency of the model (accuracy +25 points, `not_applicable` and `unclear` recall tripled) but does not help the planted defects: defect recall changes by +0.05 and is not significant. The defects are what the model itself finds, and 40% of the planted violations are missed by it.
- **The precision of `violated` per requirement (0.44) understates the review.** About two thirds of the `violated` quotes hit a planted violation of the document (0.64), but often under a neighbouring requirement: a sentence about access to logs granted to whole teams is attached to `LOG-04` while the planted flaw belongs to another access rule; internal services reading events without credentials are attached to `AUTH-01` (external APIs) while the planted flaw is `AUTH-02`. Another source of apparent false alarms is the model: it reads "access to sensitive data is logged" as a violation of "logs must not contain sensitive data".
- **Severity** of the 43 right `violated` verdicts: exact in 40%, within one level in 95%, mean absolute error 0.65 levels (interval 0.48 to 0.83). The model rates nearly everything `high` (gold `critical`: 9 of 10 rated `high`, gold `medium`: 13 of 21 rated `high`) and almost never `low` or `critical`.
- **Confidence.** AUROC of the log-probability confidence 0.77 [0.75, 0.79]; after the layer the stored confidence is the verifier probability and has AUROC 0.65, which is not a statement about the layer.

## 10c. Full dev split: reasoning before the verdict, two runs together

The reasoning prompt of section 10.2 was run on all 96 dev documents (`dev_reasoned800`), with the verifier and the decision layer as in 10b. "Both" feeds the features of the overview run and of the reasoning run into one decision layer (`stack_verdicts.py --extra`).

| Run | Accuracy | Macro F1 | `violated` R / P | `unclear` R / P | `not_applicable` R / P | Defect recall | Violated quotes hit a planted violation (P / R) | Planted violations / ambiguities found |
|---|---|---|---|---|---|---|---|---|
| overview, model verdicts | 0.510 | 0.442 | 0.61 / 0.44 | 0.19 / 0.46 | 0.21 / 0.64 | 0.43 | 0.64 / 0.68 | 0.58 / 0.28 |
| overview + decision layer | 0.764 | 0.692 | 0.58 / 0.44 | 0.66 / 0.65 | 0.68 / 0.72 | 0.48 | 0.66 / 0.65 | 0.54 / 0.42 |
| reasoning, model verdicts | 0.580 | 0.521 | 0.61 / 0.47 | 0.47 / 0.44 | 0.21 / 0.62 | 0.60 | 0.59 / 0.64 | 0.57 / 0.63 |
| reasoning + decision layer | 0.761 | 0.703 | 0.61 / 0.54 | 0.64 / 0.64 | 0.66 / 0.72 | 0.51 | 0.67 / 0.66 | 0.57 / 0.45 |
| both runs + decision layer | 0.771 | 0.714 | 0.62 / 0.54 | 0.66 / 0.65 | 0.67 / 0.73 | 0.50 | 0.72 / 0.66 | 0.57 / 0.42 |

- Two operating points follow. For **agreement with the gold verdicts** use the decision layer (accuracy 0.76 to 0.77, macro F1 0.70 to 0.71); the combination of both runs is the best, by one point of accuracy. For **finding the planted defects** use the raw verdicts of the reasoning prompt: defect recall 0.60, planted ambiguities 0.63, because the layer, trained on all verdicts, treats the rare planted ambiguities like the many vague-policy `unclear` pairs and loses them (0.63 to 0.45).
- The precision of `violated` is best with the reasoning prompt and the layer (0.54 per requirement, 0.67 by quote); recall of `violated` stays at 0.61 in every variant: about 40% of the planted violations are not recognised by the 4B model at all.
- **Tried and dropped.** Training the layer on the nine gold subtypes instead of the four verdicts (and summing the probabilities per verdict) gives lower accuracy (0.743 to 0.747) and no better planted ambiguities (0.46). A class weight of 1 or 1.5 instead of 0.5 raises recall of `violated` (0.65 to 0.72) only at precision of 0.29 and 0.07. A separate severity call and a stated confidence were tried in section 10.1 and give no gain.

## 11. Open questions and next steps

- Verdict stage on oracle contexts: give the model the gold requirement and a context that contains the evidence (for `compliant` and `violated` the gold sentence is added to the retrieved fragments; for `unclear` and `not_applicable` no evidence sentence exists, so the real retrieved fragments are the oracle context) and measure the verdicts with the scores of section 9, to separate errors of the verdict step from errors of retrieval.
- Choose the retrieval method and the number of candidates by recall on the pairs whose gold verdict is `violated` or `unclear`, with the size of the context as the trade-off.
- Full pipeline: requirements from the best policy analysis (not the gold list), retrieval of design fragments per requirement, one verdict per requirement on the real retrieved context, derived labels (action) in code, then all scores.
- Applicability filter before the verdicts is optional, because `not_applicable` is itself a verdict; measure whether it helps.
- Measure recall@k against document length by padding dev designs with distractor sentences.
- Self-consistency, a verifier and a cascade; a plot of quality against number of LLM calls.
- Confirm the best variant on the full dev split, then open the test split once.

## 12. Reproduction

- Retrieval: `python scripts/run_retrieval.py dev`, then `python scripts/report_retrieval.py dev flaws --reference dense:qwen/w0/plain` (groups: `all`, `flaws`, `violation`, `ambiguity`, `not_clear`, `satisfied`). It needs a CUDA build of torch for reasonable speed; the Windows environment has none, so it was run in WSL with the vLLM environment plus extra packages in `/root/retrieval_extra`, with the vLLM server stopped to free the GPU.
- Wording variation: `python scripts/rephrase_satisfied.py`, then `python scripts/build_case.py <case ids>`.
- Reviewer runs: `scripts/run_baseline.py` (flags `--policy-analysis`, `--pilot`, `--topics`, `--compliant`, `--silence`), `scripts/evaluate_run.py`, `scripts/compare_runs.py`; results in `data/runs/<run>/` with the exact prompt in `run_config.json`.
- Policy analysis: `scripts/analyze_policies.py`, `scripts/score_policies.py`.
- Stored data: `data/retrieval/dev.json` (per-pair retrieval scores), `data/retrieval/rankings_dev.json` (top-20 rankings of Qwen and the hybrid, windows 0 and 1), `data/retrieval/ambiguity_probe_dev.json` (section 7).
