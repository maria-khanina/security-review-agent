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

> **Superseded metrics.** The tables of sections 10 to 10e were computed before the revision of the gold and of the headline metrics (section 10f). Their columns "defect recall", "planted violations / ambiguities found" and "precision of reports on planted defects" measure what the generator planted rather than agreement with the gold verdicts and are no longer used; their numbers are kept as a record. Section 10f has the current numbers for every variant.

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

### 10d. What the decision layer learns (ablation on the reasoning run, full dev)

Accuracy of the cross-validated layer (grouped by service, 24 features) when one group of features is left out, and when only that group is used:

| Feature group | Without it | Only it |
|---|---|---|
| all features | 0.761 | |
| topics of the requirement (12) | 0.705 | 0.513 |
| wording class of the requirement (3) | 0.738 | 0.462 |
| word overlap between the requirement and the shown fragments | 0.740 | 0.620 |
| length of the requirement | 0.751 | 0.386 |
| log-probabilities of the four verdicts (4) | 0.756 | 0.580 |
| verifier probability of yes | 0.757 | 0.492 |
| a quote was found | 0.760 | 0.599 |
| overlap between the requirement and the quote | 0.763 | 0.549 |

The gain over the raw verdicts (0.58) comes mostly from properties of the requirement and its match with the design (topics, wording, word overlap), not from the signals of the model about its own answer: the log-probabilities alone give 0.58 and removing them or the verifier costs less than half a point. In other words the layer learns the prior of this policy: which kinds of requirements are usually vague, inapplicable or stated, and that a requirement with no overlap with any fragment is not stated. This transfers to unseen services of the same policy (cross-validation by service) but not necessarily to another policy, where it has to be retrained on labelled reviews.

## 10e. Follow-up checks (full dev unless noted)

- **Was the gold sentence in the 10 retrieved chunks?** For the pairs that have a gold sentence (1353 `compliant`, 74 `violated`) it was missing in 4 pairs on dev (3 `violated`, 1 `compliant`), so retrieval at 10 candidates contains the evidence for 96% of the violations and 99.9% of the compliant statements. On the pilot only one of 474 pairs differed between the real and the oracle context (a `violated` pair judged `unclear` in both). The oracle comparison of section 10 therefore compared two almost identical runs: it shows that retrieval is not the limit, not how much the model uses the evidence. Not done: removing or moving the gold sentence inside the context.
- **Where the wrong verdicts go** (pilot, 1151 pairs, rows are gold, columns predicted `compliant` / `violated` / `unclear` / `not_applicable`):

| Gold | base | with overview | with overview and reasoning |
|---|---|---|---|
| `compliant` | 447 / 0 / 8 / 0 | 451 / 0 / 3 / 1 | 442 / 1 / 12 / 0 |
| `violated` | 1 / 16 / 1 / 1 | 1 / 14 / 2 / 2 | 0 / 13 / 5 / 1 |
| `unclear` | 154 / 10 / 80 / 50 | 190 / 9 / 49 / 46 | 94 / 9 / 145 / 46 |
| `not_applicable` | 213 / 12 / 93 / 65 | 223 / 5 / 63 / 92 | 117 / 5 / 177 / 83 |

  Half of the `unclear` and of the `not_applicable` pairs are answered `compliant` by the base run; reasoning moves part of them to `unclear`.
- **Recall of planted defects at a fixed number of false alarms** (false alarm: a gold `compliant` or `not_applicable` pair flagged by P(violated) + P(unclear) above a threshold; 145 planted defects, 2538 such pairs, 96 documents; raw verdicts):

| False alarms per document | 0.5 | 1 | 2 | 3 | 5 | 8 |
|---|---|---|---|---|---|---|
| overview run, recall of planted defects | 0.30 | 0.45 | 0.52 | 0.57 | 0.63 | 0.75 |
| reasoning run | 0.05 | 0.06 | 0.26 | 0.49 | 0.69 | 0.80 |

  The probabilities of the reasoning run are close to 1 for most flagged pairs, so low budgets cannot be set.
- **Planted defects recognised as some defect, and false alarms per document** (verdict `violated` or `unclear` on the pair of the planted flaw; violated false alarm = a `violated` quote that overlaps no planted violation):

| Run | Violations: verdict `violated` | Violations: `violated` or `unclear` | Violated quotes hitting a planted violation, recall | Ambiguities: verdict `unclear` | False alarms per document (gold compliant or not applicable flagged) | Violated quotes outside planted violations per document |
|---|---|---|---|---|---|---|
| overview, model | 0.61 | 0.77 | 0.68 | 0.28 | 2.4 | 0.39 |
| overview + layer | 0.58 | 0.80 | 0.65 | 0.42 | 3.8 | 0.32 |
| reasoning, model | 0.61 | 0.84 | 0.64 | 0.63 | 6.1 | 0.41 |
| reasoning + layer | 0.61 | 0.78 | 0.66 | 0.45 | 3.7 | 0.28 |
| both + layer | 0.62 | 0.80 | 0.66 | 0.42 | 3.6 | 0.22 |

- **Severity** of the right `violated` verdicts: mean absolute error 0.65 to 0.69 levels, exactly right in 33% to 40%.
- **A violation quoted under another requirement.** In the reasoning run 93 `violated` verdicts have a quote; 44 are right for their pair, 14 are wrong for the pair but quote a sentence that is a planted violation of another rule of the same document, 35 quote no planted violation. The 14 are mostly one bad sentence that violates two requirements (card numbers in logs against the card-data requirement and the log requirement; a public database endpoint against the port requirement and the network requirement), while the gold names only the rule the generator planted.
- **Model of the decision layer** (reasoning run, grouped by service, 5 folds): logistic regression accuracy 0.761, macro F1 0.703, `violated` 0.61 / 0.54, `unclear` 0.64 / 0.64; gradient boosting (depth 3, class-weighted) 0.854, 0.767, `violated` 0.53 / 0.50, `unclear` 0.77 / 0.78. Without topics and wording the two reach 0.630 and 0.763.
- **How far the layer transfers.** Accuracy of the raw reasoning verdicts is 0.58.

| Held-out unit | logistic: all features / without topics / without topics and wording | boosting: all / without topics / without topics and wording |
|---|---|---|
| a service | 0.761 / 0.705 / 0.630 | 0.854 / not run / 0.763 |
| a policy version (v1, v2, v3 share the same 44 rules) | 0.705 / 0.703 / 0.635 | 0.722 / 0.700 / 0.674 |
| a rule (the closest to a new policy) | 0.617 / 0.671 / 0.577 | 0.664 / 0.680 / 0.644 |

- **Verifier threshold.** The threshold of section 10 chosen on the other services of the pilot gives accuracy 0.583 (chosen on all pilot pairs 0.573, no threshold 0.528); the best threshold of the grid (0.995) is chosen in every fold.

## 10f. Results with the revised gold and metrics (superseded by 10i)

The labels and the designs were rewritten after this section (10h) and every run was repeated; the numbers below are history.

**Changes of the gold and the metrics.**
- *What counts.* A verdict is *shown* to the user when it is `violated` or `unclear`, and *dropped* when it is `compliant` or `not_applicable`; the user cannot see which of the two dropped verdicts was given. The headline scores are therefore: **recall** (gold shown pairs that the system also shows), **precision** (system shown pairs that are shown in the gold), **false alarm rate** (gold dropped pairs that the system shows) and the same count per document, and a **tolerant accuracy** over the three groups `violated` / `unclear` / dropped where confusing `violated` with `unclear` gets half credit. The four-way accuracy and the per-verdict recall and precision stay for diagnosis. The scores based on what the generator planted are removed.
- *Quote.* A quote is accepted when its token overlap with the gold sentence is at least 0.3 or when it covers at least 60% of the gold sentence.
- *Gold.* (1) A planted violation lists the other rules that its scenario also breaks (`data/policies/violation_overlaps.yaml`, 21 annotated scenarios of 258, attached to the scenario text and not to the rule): such a rule is `violated` in the gold if it was unlabeled and is left out of the scoring if the design also states it as satisfied or if the rule does not apply (5 pairs on dev). (2) The 580 dev pairs that are inapplicable only because each service has a single exposure value are left out of the scoring. The scored dev pairs are 2998 (of 3583): 1353 `compliant`, 1186 `not_applicable` minus the left-out ones, 968 `unclear`, 76 `violated`.

Pilot (30 documents, 961 scored pairs):

| Variant | Recall | Precision | F1 | False alarm rate / per document | Tolerant accuracy | Four-way accuracy | `violated` R / P | `unclear` R / P |
|---|---|---|---|---|---|---|---|---|
| base | 0.34 | 0.70 | 0.46 | 0.069 / 1.5 | 0.733 | 0.601 | 0.84 / 0.47 | 0.27 / 0.68 |
| strict definitions | 0.44 | 0.65 | 0.53 | 0.114 / 2.5 | 0.734 | 0.621 | 0.68 / 0.50 | 0.38 / 0.60 |
| with overview | 0.24 | 0.69 | 0.35 | 0.052 / 1.1 | 0.710 | 0.586 | 0.74 / 0.54 | 0.17 / 0.60 |
| reasoning, no overview | 0.77 | 0.59 | 0.67 | 0.256 / 5.5 | 0.745 | 0.702 | 0.84 / 0.53 | 0.72 / 0.56 |
| reasoning with overview | 0.55 | 0.63 | 0.59 | 0.157 / 3.4 | 0.740 | 0.668 | 0.68 / 0.52 | 0.49 / 0.58 |
| with overview + decision layer | 0.72 | 0.74 | 0.73 | 0.122 / 2.6 | 0.820 | 0.787 | 0.68 / 0.50 | 0.68 / 0.72 |
| reasoning with overview + decision layer | 0.69 | 0.75 | 0.72 | 0.113 / 2.4 | 0.816 | 0.790 | 0.68 / 0.48 | 0.65 / 0.73 |

Full dev (96 documents, 2998 scored pairs):

| Variant | Recall | Precision | F1 | False alarm rate / per document | Tolerant accuracy | Four-way accuracy | `violated` R / P | `unclear` R / P |
|---|---|---|---|---|---|---|---|---|
| with overview | 0.26 | 0.72 | 0.39 | 0.055 / 1.1 | 0.701 | 0.569 | 0.61 / 0.51 | 0.19 / 0.64 |
| reasoning with overview | 0.53 | 0.65 | 0.58 | 0.151 / 3.1 | 0.729 | 0.650 | 0.61 / 0.54 | 0.47 / 0.60 |
| with overview + decision layer | 0.71 | 0.75 | 0.73 | 0.125 / 2.5 | 0.810 | 0.776 | 0.62 / 0.53 | 0.67 / 0.73 |
| reasoning with overview + decision layer | 0.69 | 0.77 | 0.73 | 0.112 / 2.3 | 0.815 | 0.786 | 0.61 / 0.61 | 0.67 / 0.74 |
| both runs + decision layer | 0.70 | 0.77 | 0.73 | 0.115 / 2.3 | 0.815 | 0.788 | 0.64 / 0.59 | 0.67 / 0.74 |

- **Raw verdicts.** The reasoning prompt without the overview gives the largest recall (0.77) and the most false alarms (5.5 per document); the overview moves answers to `not_applicable` and lowers both. At a fixed budget of false alarms the two reasoning variants are comparable (recall of shown pairs at 1, 2, 3 and 5 false alarms per document: with overview 0.24, 0.40, 0.50, 0.74; without overview 0.06, 0.24, 0.36, 0.70), so the overview mostly changes the operating point.
- **Decision layer.** At about 2.5 false alarms per document it gives recall 0.69 to 0.71 and precision 0.75 to 0.77, which none of the raw variants reaches; it is cross-validated by service but, see 10d and 10e, it carries priors of this policy.
- **Free-form reviewer.** Read as verdicts (`compare_baseline.py`), its best variant shows 3% of the pairs that are shown in the gold at a false alarm rate of 3.5%.

**Cost per document.** Three counts matter: model calls, prompt tokens (what is sent; it includes the policy requirement, the 10 fragments, the overview and the fixed instructions) and generated tokens (what the model writes). Generated tokens cost more per token than prompt tokens, because they are produced one after another while the prompt is read in one pass, so both are reported and not added. The time to an answer for one document is the sum of the call times when the calls run one after another; the 39 requirements are independent, so they can run in parallel.

Measured on three pilot documents with an otherwise idle vLLM server (Qwen3-4B-AWQ on an 8 GB GPU, at most two requests at once, calls one after another):

| Variant | LLM calls | Prompt tokens | Generated tokens | Seconds |
|---|---|---|---|---|
| base | 39.7 | 30,400 | 2,500 | 44 |
| base + verifier | 79.3 | 45,500 | 2,700 | 54 |
| reasoning with overview | 39.7 | 38,600 | 3,300 | 58 |
| reasoning with overview + verifier | 79.3 | 53,800 | 3,600 | 68 |

On the 30 pilot documents the tokens rebuilt from the stored prompts (without the chat template, about 3% lower) are 29,500 / 2,400 for the base run, 37,000 / 2,300 with the overview and 38,000 / 3,500 for reasoning with overview. The verifier doubles the number of calls but adds only about ten seconds, because its answer is two words long and its prompt starts with the same fixed text. The policy analysis (one call per policy version) and the ranking of the design chunks (one pass of the embedding model per document) are not included; the decision layer costs no model calls.

## 10g. Audit of the gold labels (reasoning run, full dev)

Method: a sample of pairs where the model disagrees with the gold (missed planted violations and ambiguities, `violated` answers that the gold does not expect, `stated` pairs answered `unclear`, component-driven `not_applicable` answered `compliant`, `drift_claim`) was read against the design text, and every pair of the subtypes that claim silence was checked with a lexical test: does any design sentence outside the gold span contain at least half of the content words of the requirement.

Lexical test, pairs per subtype with such a sentence: `vague_policy` 3 of 856, `not_in_service` 0 of 507, `implementation_only` 0 of 96, `planted_violation` 1 of 74 (c023 API-05, a sentence about replaced queries, not a statement of the rule), `planted_ambiguity` 0 of 71, `coupled_silence` 1 of 41 (c095 CRYPTO-01, a partial statement about secrets). The claim of silence therefore holds for 40 of 41 coupled-silence pairs. The test is lexical and finds only statements that reuse the wording of the requirement.

Problems that remain although the plan is scripted (only the prose is free):

1. **Specifics of the policy sentence missing from a generic statement.** About 86 of 1322 `stated` pairs: the policy version asks for more than the stored statement says (HMAC with a timestamp, plain environment variables, ten consecutive failures, key management in CRYPTO-01 v2). The gold `compliant` is then only partly true.
2. **Applicability by facts, not by text.** Component-driven `not_applicable` is unreliable where the rule generalises beyond the component: LOG-04 (`log_pipeline`, 65 pairs) and the rules for personal data when the service also holds card data (DATA-01, DATA-02, DATA-03, DATA-05, CRYPTO-01). Together with NET-02, NET-05, AUTH-05 and CRYPTO-02 there are 450 component-driven pairs on dev.
3. **Incidental contradictions in the prose** (c070 LOG-01) and **exception sentences that inherit the verdict of the rule** (c086 LOG-03).
4. **Missing overlaps:** NET-01 scenarios 0 to 5 also break NET-03.
5. **Unplanted violations** remain possible; the model's `violated` answers outside the planted spans include real ones.

Next: add the NET-01 overlaps, mark the `stated` pairs with unmet specifics as contested, widen the exclusion of unreliable component-driven pairs, then re-score. The sentence-boundary overview fix is also open.

## 10h. Labels and designs rewritten (2026-10-24, evening)

The audit of 10g and the discussion that followed changed the principle behind the gold: **the label is what a careful reader of the design text alone concludes.** A fact that only the generator knows (the exposure of the service, whether a component exists) counts only if the text makes it plain. A rule that names a value (a limit, a period, a count) is satisfied only by a design that gives a concrete value; "the API has rate limits" is not enough. The wording "should" is only phrasing and counts as a requirement. Only really vague wording (appropriate, timely) and conflicting wording give `unclear`.

**Gold subtypes now** (dev, 3583 pairs, 3541 scored): `stated` 1692 (compliant), `planted_violation` 137 and `co_violation` 3 (violated), `no_external_callers` 195 and `not_in_service` 363 and `implementation_only` 96 (not applicable), `vague_policy` 644 and `soft_violation` 18 (a violation of a vague wording) and `planted_ambiguity` 71 and `partial_statement` 9 (the statement lacks a named value) and `unplanned_applicable` 155 and `exposure_silence` 173 and `coupled_silence` 27 (all `unclear`, the design is silent about an applicable rule). The proportions of the scored pairs are compliant 47.7%, unclear 29.9%, not applicable 18.4%, violated 3.9% (test split: 43.5%, 33.4%, 19.4%, 3.7%).

**Exclusions** (42 pairs on dev, 1.2%): a pair is left out when a design sentence repeats at least half of the content words of a requirement the gold calls silent, when the prose still holds a claim sentence left from the removed drift (`removed_claims.yaml`), when a violation scenario does not break the wording of the policy version, or when a violation of one rule also breaks another rule (the overlap table).

**What changed in the generator.** Drift mutations, drift flaws and their configuration are gone. Satisfied statements are written per policy version: `strict_phrasings` and `required_terms` in `compliant_phrasings.yaml` for the rules whose version names something the general wording lacks (the number of failures, HMAC and timestamp, key management, the rate limit, the retention period, the expiry of exports). Violation scenarios that do not break the wording of a version are skipped for it (`misfits`). Applicability: AUTH-02 and CRYPTO-04 now concern every service, AUTHZ-01, API-01 and API-04 every service that accepts requests (a new field `accepts_requests`), and the service kind alone no longer decides LOG-04 and NET-05. The exposure pairs are decided per document by an audit of the 53 internal dev documents (`exposure_audit.yaml`): 47 make plain that nobody outside the platform calls the service, 5 do not say who calls the API, 1 contradicts it.

**What changed in the designs** (all 132 documents, the prose was kept): 85 weak statements were replaced by the strict wording of the version, 284 plus 297 statements were added for applicable rules the design had not named (75% of the gaps, in the form of the document: a bullet next to a bullet, a chat message by the same speaker, a paragraph), and 111 violations were written into the designs in the voice of each author (82 dev, 29 test, 62 rules, at most 10 per rule). The implementation files were rebuilt without the drift mutations. The gate for the share of non-clear flaws fell from 0.25 to 0.15, because the added violations concern firm rules.

**Prompt.** The verdict prompt no longer says that advice-only wording gives `unclear`, states that "should" is "must", asks for the concrete values a requirement names, and lets `not_applicable` cover external-caller requirements when the design makes plain that only internal services call the service.

**Runs.** The old runs `dev_*` and `pilot_*` were made on the old texts and are stale. The new ones are called `dev2_*`; the rankings of the design sentences were recomputed.

## 10i. Results on the rewritten data (2026-10-25)

Everything below was measured after the rewrite of the labels and the designs of 10h. The old tables of 10b to 10f belong to the old labels and are kept only as history. The models, the retrieval (Qwen3-Embedding-0.6B, one sentence per chunk, 10 fragments) and the prompt are the ones of section 10, except for the three changes of the prompt listed in 10h. Dev is the 96 documents of the first 12 services (3583 pairs, 3541 scored: 1689 compliant, 1060 unclear, 653 not applicable, 139 violated), v4 is the new policy with 24 new documents (384 pairs).

**Terms.** *Shown* means that the pipeline answers `violated` or `unclear` for a requirement, which is what the reviewer of the design sees. *Recall* is the share of the requirements that should be shown (`violated` or `unclear` in the gold) which are shown, *precision* the share of the shown requirements that should be shown, *false alarm rate* the share of the requirements that should be dropped (`compliant` or `not_applicable`) which are shown. *Tolerant accuracy* counts a swap between `violated` and `unclear` as half right. *Layer* is the logistic regression over the signals of the model; here it is always trained and applied with cross-validation over services (dev) or trained on dev and applied to v4.

### Does the service overview help? (dev, raw answers, no layer)

| | Without overview | With overview of 800 characters |
|---|---|---|
| Short reason (25 words) | accuracy 0.648, tolerant 0.741, shown recall 0.49 / precision 0.69, 2.7 false alarms per document | 0.654, 0.738, 0.39 / 0.74, 1.7 |
| Reasoning before the verdict (60 words) | 0.724, 0.768, 0.78 / 0.65, 5.3 | 0.713, 0.762, 0.62 / 0.68, 3.6 |

The overview does not raise the accuracy (the tolerant accuracy moves by 0.003 and 0.006, inside the interval of about 0.015). It moves the operating point: fewer false alarms and a lower recall. On the new policy v4 the same holds (below). The honest reading is that the overview of the first 800 characters is a cheap way to trade recall for precision, not a source of understanding.

### The decision layer on dev (cross-validation over services)

| Variant | Accuracy | Tolerant | Shown recall / precision | False alarms per document |
|---|---|---|---|---|
| raw, overview and reasoning | 0.713 | 0.762 | 0.62 / 0.68 | 3.6 |
| layer, all 24 features | 0.798 | 0.827 | 0.72 / 0.78 | 2.5 |
| layer without the wording of the requirement (21) | 0.784 | 0.814 | 0.69 / 0.77 | 2.6 |
| layer independent of the policy (9: log-probabilities, verifier, quote found, word overlap with fragments and quote, length) | 0.761 | 0.789 | 0.75 / 0.69 | 4.2 |

### The unseen policy v4 (384 pairs, 24 new documents, layer trained on dev only)

Gold: 29 `violated`, 119 `unclear`, 70 `compliant`, 166 `not_applicable`. The shares differ from dev (more `not_applicable`, fewer `compliant`) because the 15 new rules apply to few services each.

| Variant | Accuracy | Tolerant | Shown recall / precision | False alarms per document |
|---|---|---|---|---|
| raw, no overview, short reason | 0.643 | 0.721 | 0.65 / 0.71 | 1.7 |
| raw, overview, short reason | 0.646 | 0.706 | 0.56 / 0.68 | 1.7 |
| raw, no overview, reasoning | 0.622 | 0.660 | 0.66 / 0.58 | 2.9 |
| raw, overview, reasoning | 0.664 | 0.688 | 0.57 / 0.64 | 2.0 |
| layer, all features | 0.513 | 0.573 | 0.85 / 0.51 | 5.0 |
| layer without wording | 0.664 | 0.724 | 0.74 / 0.71 | 1.9 |
| layer independent of the policy | 0.651 | 0.672 | 0.71 / 0.58 | 3.1 |

- The layer with all features **collapses** on the new policy (accuracy 0.51). The reason is the wording feature: the model that reads the policy called all 11 clear requirements of v4 `vague_or_advisory` (the wording classification of the policy analysis was tuned on v1 to v3), and the layer had learned that "vague" means `unclear`. The topics are also read worse (the share with at least one correct topic 0.69, the overlap with the gold 0.375, on v1 to v3 it was 0.9 and 0.6).
- Without the wording the layer keeps the accuracy of the raw answers (0.664) and raises the quality of what the reviewer sees: the F1 of the shown requirements is 0.726 against 0.602 (paired bootstrap over documents, significant), with the same false alarms. The price is the precision of `violated`: 0.26 against 0.72 (the layer calls many `unclear` pairs `violated`; also significant). The two numbers say the layer is useful for deciding what to show and not useful for telling a violation from an ambiguity.
- The layer independent of the policy is the safest claim about transfer. It does not hold the whole gain (accuracy 0.651 against 0.664 for the raw answers), it shows more (recall 0.71) and raises more false alarms.
- The sample is small: 384 pairs, 24 documents, intervals of the accuracy about plus and minus 0.04. Differences of one to two points are noise.

### The cascade: calls only where the cheap prediction is unsure

A layer on the features that exist before any model call (word overlap, length, topics; the wording was left out) predicts the verdict; the pairs where its largest class probability is lowest are sent to the model, and for them the layer over all signals decides.

| Share of pairs sent to the model | Dev accuracy | Dev shown recall / precision | v4 accuracy | v4 shown recall / precision |
|---|---|---|---|---|
| 0 (no model call at all) | 0.720 | 0.67 / 0.69 | 0.560 | 0.80 / 0.61 |
| 0.2 | 0.781 | 0.71 / 0.74 | 0.604 | 0.81 / 0.67 |
| 0.4 | 0.794 | 0.71 / 0.78 | 0.638 | 0.83 / 0.72 |
| 0.6 | 0.799 | 0.71 / 0.78 | 0.654 | 0.82 / 0.71 |
| 1.0 | 0.798 | 0.72 / 0.78 | 0.664 | 0.74 / 0.71 |

- On dev, 40% of the model calls give the same accuracy as all calls (0.794 against 0.798). Choosing the pairs by the confidence of the cheap layer matters: 50% of the pairs chosen at random give 0.759.
- **The warning:** a layer that never calls the model reaches 0.720 on dev, as much as the raw answers of the model with reasoning (0.713). Most of the accuracy on dev is the prior of the policy (which kinds of requirements are usually vague, stated or inapplicable), not reading of the design. On v4 the same prior gives 0.560, and without the topics 0.424. This is why the numbers on dev alone would overstate the pipeline, and why v4 exists.
- On v4 the cascade keeps its worth (sending 40% to 60% of the pairs gives the recall and the precision of the whole), but the sample is small.

### Several requirements in one call (dev, overview, short reason, groups by the first predicted topic)

| Requirements per call | Calls per document | Prompt tokens | Seconds | Accuracy | Tolerant | Shown recall / precision | Quote found |
|---|---|---|---|---|---|---|---|
| 1 | 38.1 | 42,400 | 54 | 0.699 | 0.748 | 0.40 / 0.77 | 0.596 |
| 2 | 19.3 | 24,200 | 46 | 0.672 | 0.741 | 0.40 / 0.74 | 0.567 |
| 4 | 9.8 | 14,100 | 43 | 0.685 | 0.752 | 0.44 / 0.75 | 0.563 |
| 8 | 5.4 | 8,700 | 42 | 0.658 | 0.736 | 0.39 / 0.72 | 0.528 |

Four requirements per call cut the calls by four and the prompt tokens by two thirds with no loss of the tolerant accuracy (0.752 against 0.748); eight per call lose about one point. The quotes suffer first: the share of right verdicts with a quote that the design confirms falls from 0.60 to 0.53. The topics used for the groups are the predicted ones. The time falls little because the generation of the answers, not the reading of the prompt, takes most of it.

### Length of the design: the top 10 fragments against the whole document

The same 24 designs of about 700 words and their long versions of about 3500 words (the added text has no security content, so the gold is unchanged), reasoning with overview.

| | 700 words | 3500 words | 10,000 words (6 other designs) |
|---|---|---|---|
| top 10 fragments: accuracy / tolerant | 0.720 / 0.759 | 0.724 / 0.774 | 0.686 / 0.748 |
| top 20 fragments | 0.732 / 0.769 | 0.742 / 0.778 | |
| whole document in every call | **0.751 / 0.780** | 0.722 / 0.750 | does not fit in the 12,000-token window |
| prompt tokens per document, top 10 / whole | 41,000 / 76,000 | 40,500 / 256,000 | |
| seconds per document, top 10 / whole | 58 / 83 | 58 / 180 | |

Paired bootstrap over the 24 documents: at 700 words the whole document is better than the top 10 fragments in the strict accuracy (+0.031, interval 0.006 to 0.058), but not significantly in the tolerant accuracy (+0.021, interval -0.004 to +0.046) or in the recall of the shown requirements (+0.039, interval -0.027 to +0.107); at 3500 words it is not better (tolerant accuracy -0.025, interval -0.051 to +0.002; recall -0.061, interval -0.136 to +0.006) and costs six times the tokens. The top 10 fragments keep their quality as the design grows (tolerant 0.759 at 700 words, 0.774 at 3500, 0.748 at 10,000, different documents at the last point) and the cost stays flat. What is established is the cost; the quality difference between the two ways is within the noise, with the whole document possibly slightly better at 700 words and slightly worse at 3500.

### Cost per document (measured, vLLM, Qwen3-4B-AWQ, one 8 GB GPU, calls one after another)

| Variant | Calls | Prompt tokens | Generated tokens | Seconds |
|---|---|---|---|---|
| short reason, no overview | 38.1 | 32,800 | 2,400 | 44 |
| short reason, overview | 38.1 | 40,100 | 2,300 | 45 |
| + verifier | 76.1 | 55,800 | 2,600 | 55 |
| reasoning, no overview | 38.1 | 33,800 | 3,500 | 60 |
| reasoning, overview | 38.1 | 41,000 | 3,300 | 65 |
| 4 requirements per call | 9.8 | 14,100 | 2,500 | 43 |
| 8 requirements per call | 5.4 | 8,700 | 2,400 | 42 |

The verifier doubles the calls and gives nothing on the new data: the layer reaches 0.797 without it against 0.798 with it. The log-probabilities of the verdicts add about 2.5 points (0.773 without them), and all signals of the model together (log-probabilities, verifier, quote) about 8 points (0.720 without them). The requirements per call are counted as 38 because the policy has 38 sentences on average per policy version; the cost grows with the number of requirements, not with the length of the design.

## 10j. Wording of the requirements judged one by one (2026-10-25)

The collapse of the layer on v4 (10i) comes from the wording class of the requirements. The analysis of the policy asks one call to list all requirements with their loose phrases, and on v4 it called all 11 clear requirements vague (agreement with the gold wording over the four policies 0.69; on v4 4 of 16). A new step judges every requirement sentence in its own call: the model lists the words that leave the measure to the reader (words that say how much, how often, how fast or how well without a number, a named mechanism or a named standard; "must", "should", numbers, named mechanisms and prohibitions are declared not vague), code keeps the phrases that occur in the sentence and are not modal verbs, and a sentence with such a phrase is `vague_or_advisory`. The contradictory wording is taken over from the first analysis. The cost is one short call per requirement and policy, about 130 calls once.

The prompt has **no example phrases**. A first version listed examples ("appropriate", "regularly", "excessive", "long enough" and others); it reached 0.859 agreement and 16 of 16 on v4, but I had written that list after reading all four policies, so it was removed and the step repeated.

| | Agreement with the gold wording (4 policies, 128 requirements) | v4 | Vague requirements found | Clear requirements called vague |
|---|---|---|---|---|
| one call for the whole policy | 0.688 | 4 of 16 | 7 of 18 | 17 of 96 |
| one call per requirement, no examples | 0.742 | 15 of 16 | 15 of 18 | 18 of 96 |

The step finds twice as many vague requirements and keeps the number of false "vague" about equal. Contradictions are found no better than before (2 of 12; the gold counts both sentences of a conflicting pair).

Effect on the layer with all features (trained on dev, applied to v4): accuracy 0.648 (it was 0.513), tolerant 0.703, shown recall 0.72 and precision 0.67 at 2.2 false alarms per document; on dev with cross-validation 0.810 (it was 0.798). On v4 this is not better than the layer without the wording (0.664, tolerant 0.724, 0.74 / 0.71 at 1.9 false alarms); the wording feature no longer breaks the layer but does not help it there.

## 10k. The final comparison on the unseen policy v4 (2026-10-25)

The question of this section is which variant is best on v4, not how much worse v4 is than dev. Every variant that has a layer is trained on the dev run of the same configuration (96 documents, policies v1 to v3) and applied to the 24 documents of v4 (384 pairs; 29 `violated`, 119 `unclear`, 70 `compliant`, 166 `not_applicable`). Nothing was tuned on v4: the choice of features, presets and prompts was made earlier, with one exception that has to be said: the example phrases were removed from the wording prompt after the first look at v4 and the step was repeated (10j).

**Columns.** *Shown recall* and *precision*: the share of the requirements that should be shown to the reviewer (`violated` or `unclear` in the gold) that are shown, and the share of the shown ones that should be. *False alarms per document*: shown requirements that should be dropped (`compliant`, `not_applicable`), per document. *Recall at 0.5 / 1 / 2 / 3 false alarms per document*: the requirements are sorted by the probability of being shown (for the raw answers the probability that the model gives to `violated` and `unclear` at the verdict token, for a layer its class probabilities), and the recall is read at the point where the false alarms reach half, one, two and three per document. *Tolerant accuracy*: right verdict, or both dropped, or a swap between `violated` and `unclear` counted as half. Intervals are 95% percentiles of 300 resamples of the 24 documents; the intervals of different rows overlap heavily, so differences of a few points between neighbouring rows are not established. The cost is measured per document on the v4 run (16 requirements per document, so about 2.4 times cheaper than on dev); a layer adds no model call, the cascade is charged for the pairs it sends.

**Variants.** A: short reason (25 words), no overview. B: short reason, overview of 800 characters. C: reasoning (60 words), no overview. D: reasoning, overview. E: reasoning, architecture card instead of the overview (see the last part of this section). *Layer*: logistic regression over the signals of the model and the properties of the requirement; *no_wording* leaves out the wording class, *agnostic* keeps only the signals of the model, the word overlap and the length, *all (first wording)* uses the wording of the one-call policy analysis, *all (wording per req.)* the wording judged requirement by requirement (10j). *Prior only*: the layer on the word overlap with the shown fragments, the length and the topics, with no model call. *Cascade*: the prior decides, and the share of the pairs where it is least sure is sent to the model, whose signals go to the layer *no_wording*.

| Variant | Shown recall (95% interval) | Shown precision | False alarms per document | Recall at 0.5 / 1 / 2 / 3 false alarms per document | Accuracy | Tolerant accuracy | Calls | Prompt tokens | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| A short reason, no overview: raw | 0.65 (0.59 to 0.71) | 0.71 | 1.67 | 0.27 / 0.43 / 0.67 / 0.72 | 0.643 | 0.721 | 16.0 | 13,963 | 18 |
| A short reason, no overview: layer without the wording | 0.80 (0.75 to 0.84) | 0.71 | 2.00 | 0.32 / 0.41 / 0.80 / 0.93 | 0.641 | 0.721 | 16.0 | 13,963 | 18 |
| A short reason, no overview: layer independent of the policy | 0.87 (0.84 to 0.91) | 0.54 | 4.58 | 0.39 / 0.44 / 0.57 / 0.71 | 0.578 | 0.622 | 16.0 | 13,963 | 18 |
| A short reason, no overview: layer, all features (first wording) | 0.95 (0.91 to 0.97) | 0.51 | 5.71 | 0.16 / 0.32 / 0.61 / 0.83 | 0.505 | 0.565 | 16.0 | 13,963 | 18 |
| A short reason, no overview: layer, all features (wording per requirement) | 0.82 (0.77 to 0.85) | 0.64 | 2.88 | 0.58 / 0.62 / 0.82 / 0.89 | 0.609 | 0.684 | 16.0 | 13,963 | 18 |
| B short reason, overview: raw | 0.56 (0.48 to 0.62) | 0.67 | 1.67 | 0.22 / 0.34 / 0.60 / 0.68 | 0.646 | 0.706 | 16.0 | 16,970 | 19 |
| B short reason, overview: layer without the wording | 0.80 (0.76 to 0.85) | 0.67 | 2.42 | 0.22 / 0.51 / 0.71 / 0.91 | 0.635 | 0.707 | 16.0 | 16,970 | 19 |
| B short reason, overview: layer independent of the policy | 0.71 (0.65 to 0.76) | 0.60 | 2.92 | 0.28 / 0.34 / 0.60 / 0.68 | 0.651 | 0.680 | 16.0 | 16,970 | 19 |
| B short reason, overview: layer, all features (first wording) | 0.86 (0.81 to 0.91) | 0.52 | 4.96 | 0.16 / 0.36 / 0.48 / 0.77 | 0.518 | 0.578 | 16.0 | 16,970 | 19 |
| B short reason, overview: layer, all features (wording per requirement) | 0.75 (0.69 to 0.81) | 0.71 | 1.92 | 0.43 / 0.51 / 0.77 / 0.86 | 0.661 | 0.725 | 16.0 | 16,970 | 19 |
| C reasoning, no overview: raw | 0.66 (0.60 to 0.72) | 0.58 | 2.92 | 0.04 / 0.21 / 0.55 / 0.67 | 0.622 | 0.660 | 16.0 | 14,363 | 25 |
| C reasoning, no overview: layer without the wording | 0.68 (0.63 to 0.74) | 0.67 | 2.04 | 0.25 / 0.39 / 0.66 / 0.83 | 0.651 | 0.704 | 16.0 | 14,363 | 25 |
| C reasoning, no overview: layer independent of the policy | 0.68 (0.61 to 0.74) | 0.51 | 3.96 | 0.29 / 0.39 / 0.47 / 0.56 | 0.565 | 0.600 | 16.0 | 14,363 | 25 |
| C reasoning, no overview: layer, all features (first wording) | 0.85 (0.81 to 0.88) | 0.51 | 5.12 | 0.14 / 0.30 / 0.50 / 0.67 | 0.552 | 0.589 | 16.0 | 14,363 | 25 |
| C reasoning, no overview: layer, all features (wording per requirement) | 0.72 (0.65 to 0.78) | 0.67 | 2.21 | 0.32 / 0.45 / 0.70 / 0.78 | 0.682 | 0.721 | 16.0 | 14,363 | 25 |
| D reasoning, overview: raw | 0.57 (0.51 to 0.62) | 0.64 | 1.96 | 0.22 / 0.36 / 0.57 / 0.64 | 0.664 | 0.688 | 16.0 | 17,370 | 25 |
| D reasoning, overview: layer without the wording | 0.74 (0.68 to 0.79) | 0.71 | 1.88 | 0.32 / 0.44 / 0.74 / 0.87 | 0.664 | 0.723 | 16.0 | 17,370 | 25 |
| D reasoning, overview: layer independent of the policy | 0.71 (0.65 to 0.77) | 0.58 | 3.17 | 0.39 / 0.45 / 0.57 / 0.68 | 0.648 | 0.669 | 16.0 | 17,370 | 25 |
| D reasoning, overview: layer, all features (first wording) | 0.84 (0.82 to 0.87) | 0.51 | 4.96 | 0.21 / 0.30 / 0.60 / 0.74 | 0.518 | 0.574 | 16.0 | 17,370 | 25 |
| D reasoning, overview: layer, all features (wording per requirement) | 0.73 (0.69 to 0.77) | 0.66 | 2.29 | 0.51 / 0.58 / 0.78 / 0.86 | 0.648 | 0.701 | 16.0 | 17,370 | 25 |
| E reasoning, architecture card: raw | 0.72 (0.66 to 0.79) | 0.56 | 3.54 | 0.09 / 0.36 / 0.46 / 0.70 | 0.612 | 0.645 | 16.0 | 16,973 | 26 |
| E reasoning, architecture card: layer without the wording | 0.72 (0.65 to 0.78) | 0.63 | 2.54 | 0.29 / 0.54 / 0.66 / 0.80 | 0.622 | 0.681 | 16.0 | 16,973 | 26 |
| E reasoning, architecture card: layer independent of the policy | 0.80 (0.75 to 0.84) | 0.59 | 3.42 | 0.38 / 0.45 / 0.51 / 0.62 | 0.648 | 0.681 | 16.0 | 16,973 | 26 |
| E reasoning, architecture card: layer, all features (first wording) | 0.82 (0.77 to 0.88) | 0.51 | 4.92 | 0.20 / 0.41 / 0.51 / 0.75 | 0.518 | 0.573 | 16.0 | 16,973 | 26 |
| E reasoning, architecture card: layer, all features (wording per requirement) | 0.73 (0.65 to 0.80) | 0.73 | 1.67 | 0.53 / 0.59 / 0.75 / 0.81 | 0.690 | 0.745 | 16.0 | 16,973 | 26 |
| prior only, no model call | 0.80 (0.74 to 0.87) | 0.61 | 3.17 | 0.14 / 0.36 / 0.60 / 0.79 | 0.560 | 0.646 | 0.0 | 0 | 0 |
| cascade, 40% of the pairs sent to the model | 0.83 (0.77 to 0.89) | 0.72 | 2.04 | 0.23 / 0.45 / 0.82 / 0.90 | 0.638 | 0.724 | 6.4 | 6,948 | 10 |
| cascade, 60% of the pairs sent to the model | 0.81 (0.76 to 0.86) | 0.71 | 2.04 | 0.25 / 0.32 / 0.80 / 0.89 | 0.654 | 0.727 | 9.6 | 10,422 | 15 |

**Reading.**

- **Raw answers.** The best raw variant is A, the cheapest: recall 0.65 at precision 0.71 and 1.7 false alarms per document. Reasoning (C, D) and the overview (B, D) do not improve what the reviewer sees; reasoning without the overview (C) shows more and raises more false alarms (2.9 per document).
- **The layer.** The layer without the wording class (*no_wording*) is the safe choice: for A it raises the recall from 0.65 to 0.80 at the same precision (0.71) and 2.0 false alarms per document, and the recall at three false alarms per document from 0.72 to 0.93; for D the same direction (0.57 to 0.74). The layer with the wording of the one-call analysis is bad on every configuration (precision 0.51, 5 false alarms per document): it learned on v1 to v3 that "vague" means `unclear`, and on v4 everything is called vague. The wording judged per requirement removes the damage and is the best layer on the configurations with the overview and the card; the *agnostic* layer is mostly worse than *no_wording* because it has no knowledge of the topics.
- **Best rows.** By the recall at two or three false alarms per document, the best are A with the layer without the wording (0.80 and 0.93), A with the wording per requirement (0.82 and 0.89) and the cascade that sends 40% of the pairs to the model (0.82 and 0.90). By precision at a low number of false alarms, E with the wording per requirement (precision 0.73 at 1.7 false alarms; tolerant accuracy 0.745, the highest). The differences between these rows are inside the intervals, so on 24 documents they are one group; what is clear is the distance from this group to the raw answers (recall 0.57 to 0.66 at the same precision) and to the layer with the first wording.
- **The prior alone** (no model call) shows 0.80 of what should be shown with precision 0.61 and 3.2 false alarms per document. It is not a reviewer, but it is the baseline that the layer must beat; the best rows beat it in precision (0.71 against 0.61) at 2.0 false alarms against 3.2.
- **The cascade** with 40% of the pairs sent to the model has the quality of the best layers with 6.4 calls per document instead of 16 and 7,000 prompt tokens instead of 17,000.
- **Cost.** The raw answers cost 14,000 to 17,400 prompt tokens, 1,000 to 1,500 generated tokens and 18 to 26 seconds per document on v4; the layers and the prior add nothing; the cascade 40% costs 6.4 calls and 10 seconds.


**Recall at half a false alarm per document.** This is the strict end of the scale, and it is weak for every variant: 0.58 at best (A with the layer that has the wording per requirement), 0.53 for E with the same layer, 0.51 for D, and 0.14 to 0.43 for the others; the raw answers of A, B, C, D reach 0.27, 0.22, 0.04 and 0.22. The cascade (0.23) and the layer without the wording (0.32 for A) are good at two to three false alarms per document and poor at half of one: their ranking of the pairs by the probability of being shown is not sharp at the top. If a reviewer can accept only about one false alarm in two documents, no variant here is usable; at two false alarms per document the best variants find 0.80 of what should be shown.

### Top 10, top 20 and the whole document by the length of the design (recall at 2 false alarms per document)

Thirds of v4 by the length of the design (8 designs each) and, on dev, 24 base designs against the same designs extended to about 3,500 words (the gold is the same).

| Group of designs | Words per design | Designs | Context | Shown recall | Shown precision | False alarms per document | Recall at 0.5 / 1 / 2 / 3 false alarms per document |
|---|---|---|---|---|---|---|---|
| v4, shortest third | 368 | 8 | top 10 | 0.61 | 0.64 | 2.00 | 0.28 / 0.41 / 0.61 / 0.74 |
| v4, shortest third | 368 | 8 | top 20 | 0.54 | 0.66 | 1.62 | 0.24 / 0.48 / 0.63 / 0.76 |
| v4, shortest third | 368 | 8 | whole document | 0.59 | 0.63 | 2.00 | 0.37 / 0.43 / 0.59 / 0.63 |
| v4, middle third | 522 | 8 | top 10 | 0.47 | 0.66 | 1.50 | 0.20 / 0.37 / 0.49 / 0.59 |
| v4, middle third | 522 | 8 | top 20 | 0.45 | 0.65 | 1.50 | 0.33 / 0.45 / 0.53 / 0.61 |
| v4, middle third | 522 | 8 | whole document | 0.45 | 0.71 | 1.12 | 0.37 / 0.45 / 0.51 / 0.57 |
| v4, longest third | 687 | 8 | top 10 | 0.62 | 0.63 | 2.38 | 0.19 / 0.28 / 0.55 / 0.68 |
| v4, longest third | 687 | 8 | top 20 | 0.55 | 0.74 | 1.25 | 0.25 / 0.49 / 0.57 / 0.60 |
| v4, longest third | 687 | 8 | whole document | 0.70 | 0.65 | 2.50 | 0.11 / 0.38 / 0.58 / 0.74 |
| dev, base designs | 766 | 24 | top 10 | 0.59 | 0.71 | 3.12 | 0.20 / 0.32 / 0.48 / 0.56 |
| dev, base designs | 766 | 24 | top 20 | 0.54 | 0.76 | 2.25 | 0.18 / 0.32 / 0.51 / 0.62 |
| dev, base designs | 766 | 24 | whole document | 0.62 | 0.73 | 2.92 | 0.17 / 0.33 / 0.54 / 0.64 |
| dev, same designs extended | 3512 | 24 | top 10 | 0.60 | 0.74 | 2.67 | 0.07 / 0.31 / 0.47 / 0.64 |
| dev, same designs extended | 3512 | 24 | top 20 | 0.55 | 0.77 | 2.12 | 0.21 / 0.34 / 0.50 / 0.63 |
| dev, same designs extended | 3512 | 24 | whole document | 0.54 | 0.71 | 2.83 | 0.13 / 0.26 / 0.46 / 0.55 |

At two false alarms per document the three ways stay within five points of each other in every group (0.61, 0.63, 0.59 in the shortest third of v4; 0.49, 0.53, 0.51; 0.55, 0.57, 0.58; on dev 0.48, 0.51, 0.54 for the base designs and 0.47, 0.50, 0.46 for the extended ones). The top 20 is the best or second best in four groups out of five, but with 8 to 24 designs per group none of the differences is established. There is no sign that the whole document gains from the short designs or loses at 3,500 words in this metric either; what separates the ways is the cost (the whole document needs 1.5 times the tokens at 700 words and six times at 3,500).

### The curve of the quality against the number of calls, and the context (v4)

| Variant | Shown recall (95% interval) | Shown precision | False alarms per document | Recall at 0.5 / 1 / 2 / 3 false alarms per document | Accuracy | Tolerant accuracy | Calls | Prompt tokens | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 requirement per call (list format) | 0.40 (0.33 to 0.46) | 0.77 | 0.75 | not ranked | 0.674 | 0.701 | 16.0 | 17,962 | 26 |
| 2 requirements per call | 0.47 (0.40 to 0.56) | 0.76 | 0.92 | not ranked | 0.685 | 0.717 | 8.0 | 10,225 | 22 |
| 4 requirements per call | 0.46 (0.38 to 0.55) | 0.68 | 1.33 | not ranked | 0.664 | 0.694 | 4.0 | 5,857 | 19 |
| 8 requirements per call | 0.32 (0.24 to 0.41) | 0.65 | 1.08 | not ranked | 0.615 | 0.656 | 2.0 | 3,371 | 18 |
| top 10 fragments (D) | 0.57 (0.51 to 0.62) | 0.64 | 1.96 | not ranked | 0.664 | 0.688 | 16.0 | 17,370 | 25 |
| top 20 fragments | 0.51 (0.45 to 0.58) | 0.68 | 1.46 | not ranked | 0.661 | 0.695 | 16.0 | 20,992 | 30 |
| whole document | 0.58 (0.51 to 0.65) | 0.66 | 1.88 | not ranked | 0.664 | 0.695 | 16.0 | 25,576 | 32 |

The first four rows group the requirements of a policy by their first predicted topic and put 1, 2, 4 or 8 of them into one call (short reason, overview). Two per call give the same quality as one per call (tolerant accuracy 0.717 against 0.701; the shown recall 0.47 against 0.40) at half the calls; four per call lose about two points of the tolerant accuracy and raise the false alarms; eight per call lose about five points and the recall (0.32). The last four rows keep one call per requirement and change what is shown: on v4 (about 700-word designs) top 10, top 20 and the whole document are equal inside the noise (tolerant accuracy 0.688, 0.695, 0.695; the whole document costs 1.5 times the tokens). The experiment on dev designs (10i) shows the same at 700 words; at 3,500 words the whole document is not better than the top 10 fragments, at six times the tokens.

### The architecture card (E) in numbers

The card of a design is one extra model call per design and four lines in the prompt. The model fills the exposure of the service wrongly: on the 96 dev cards 44 of the 53 internal services are called external (exposure right in 54%, which is no better than always answering "external"); the fields that serve requests are right in 79%, the data classes agree with the gold with a Jaccard of 0.29, the kinds of components are found with a recall of 0.74 and a precision of 0.97. On dev the raw answers with the card are about equal to those with the overview or without it (accuracy 0.734, tolerant 0.779, shown recall 0.72 and precision 0.68 at 4.3 false alarms per document; the overview gives 0.713, 0.762, 0.62 / 0.68, 3.6; no overview 0.724, 0.768, 0.78 / 0.65, 5.3). On v4 the raw answers with the card are worse than with the overview (accuracy 0.612 against 0.664; 3.5 against 2.0 false alarms per document). With the layer that has the wording per requirement the card row is the best by precision and tolerant accuracy (0.73 and 0.745); I do not trust this single row, since the card is wrong about the exposure, and read it as noise in a group of rows that are equal within their intervals.

## 10l. Second unseen policy v5: what is fixed before it is opened (2026-10-25)

The 24 designs of v4 cannot separate the best variants of 10k (intervals of the recall of plus and minus 0.05; the top rows are one group), and the wording step (10j) was changed after the first look at v4. A second policy, `v5`, with new rules in other areas (privacy rights, data residency, change management, pipeline, observability, capacity) and 30 new designs is written **after** this paragraph was committed, and nothing of it is used for any choice.

**Finalists** (each is the configuration of 10k trained on the dev run of the same configuration, with the analysis of the policy `llm_analysis_v2` and, where named, the wording per requirement of `llm_analysis_w2`):
1. A, raw (short reason, no overview).
2. A + layer without the wording class.
3. A + layer, wording per requirement.
4. B + layer, wording per requirement.
5. D + layer without the wording class.
6. D, raw.
7. Layer only, no model call.
8. Cascade, 40% of the pairs sent to the model (D, layer without the wording).

**What is compared.** The recall of the shown requirements at 2 false alarms per document (the primary number), the shown precision and recall at the false alarms of the decisions, the recall at half and at one false alarm per document, the cost. Paired bootstrap over documents for the differences between finalists, on v5 alone and on v4 and v5 together (54 designs). The best variant is the one with the highest recall at 2 false alarms per document among those with a shown precision of 0.65 or more on v4 and v5 together; if the paired intervals of two variants contain zero, the cheaper one is named.

## 11. State and next steps

**State (2026-10-25).** Done on dev and on the unseen policy v4: gold labels by the rule "what a careful reader concludes" (10h), designs rewritten, 111 + 34 violations authored, a policy v4 with 24 designs, raw answers in four prompt configurations and with the architecture card, the decision layer in several feature sets, the cascade, grouped requirements, top 10 against the whole document on designs up to 10,000 words, cost per document (10i to 10k). The test split (36 designs of two held-out services) has not been run.

**Known limits of the evidence.**
- v4 has 24 designs and 384 pairs; the intervals in 10k are wide, and the top rows are one group. A second new policy and more designs would be needed to rank them.
- The layer is trained on the policies v1 to v3, whose rules the designs were written for; the topics and the wording of the requirements are predictions of the model, and they are the weak point on a new policy (10j).
- The gold of `unclear` for vague policies is a convention (a vague requirement cannot be called fulfilled); about a third of the answers `compliant` on such requirements are defensible (10g).
- The designs, the violations and the statements are authored by me (an LLM) from a plan; the planted violations come from six scenario sentences per rule. The 30 long designs add reference text of the same services and appendices of neighbouring systems, not text from real documents.
- The model is Qwen3-4B-AWQ on an 8 GB GPU with a 12,000-token window; the numbers say nothing about larger models.
- The wording prompt was first written with example phrases after the policies had been read; the version in the repository has none (10j).

**Possible next steps.** A second unseen policy and 50 or more designs for it; a model of 8B or more; the applicability of a requirement decided by code from a card of the design and predicates extracted from the policy (the card of 10k is not reliable enough: its exposure is wrong for most internal services); a stronger check of the answers with a second model instead of the same model; real designs.

## 12. Reproduction

- Retrieval (section 5): `python scripts/run_retrieval.py dev`, then `python scripts/report_retrieval.py dev flaws --reference dense:qwen/w0/plain`. Needs a CUDA build of torch; the Windows environment has none, so it was run in WSL with the vLLM environment plus extra packages in `/root/retrieval_extra`, with the vLLM server stopped to free the GPU.
- Wording variation (section 6): `python scripts/rephrase_satisfied.py`, then `python scripts/build_case.py <case ids>`.
- Free-form reviewer (section 4): `scripts/run_baseline.py` (flags `--policy-analysis`, `--pilot`, `--topics`, `--compliant`, `--silence`), `scripts/evaluate_run.py`, `scripts/compare_runs.py`; results in `data/runs/<run>/` with the exact prompt in `run_config.json`. Policy analysis: `scripts/analyze_policies.py`, `scripts/score_policies.py`.
- Verdict pipeline (sections 9 to 11), in this order:
  1. `python scripts/compute_requirement_rankings.py dev llm_analysis_v2` (GPU, vLLM stopped; stores `data/retrieval/requirement_rankings_llm_analysis_v2_dev.json`).
  2. Start the vLLM server (`scripts/vllm_serve.sh Qwen/Qwen3-4B-AWQ 8000`), then `python scripts/run_verdicts.py <run> [--pilot] [--overview 800] [--reasoned] [--strict] [--oracle]`.
  3. `python scripts/run_verifier.py <run> <run>_verified` (also `--mode severity`, `--mode verbal`).
  4. `python scripts/stack_verdicts.py <run>_verified <run>_stacked [--extra <other>_verified]` (cross-validated decision layer); `python scripts/apply_stacker.py <train run> <apply run> <target>` trains on one run and relabels another.
  5. `python scripts/evaluate_verdicts.py <run> [--against <other run>]`; `python scripts/compare_baseline.py <free-form run>` scores a free-form run as verdicts.
- Policy v4 and its designs: rules in `data/policies/rules.yaml` (ids PAY, TEN, UPL, MOB, IR, TPC, DR), text `v4_platform_integrity_standard.md`, map in `policy_maps.yaml`, plan in `configs/extension_plan.yaml` (split `v4`); `python scripts/make_extension.py`, write `design_marked.md`, `python scripts/build_case.py <ids>`. Policy analysis for v4: `python scripts/analyze_policies.py llm_analysis_v2 --versions v4`; rankings: `python scripts/compute_requirement_rankings.py v4 llm_analysis_v2` (GPU, vLLM stopped; on CPU for small sets).
- Wording per requirement: `python scripts/recheck_wording.py llm_analysis_v2 llm_analysis_w2`.
- Architecture card: `python scripts/build_cards.py card_v1 --split dev`, then `python scripts/run_verdicts.py <run> --card card_v1 --reasoned`.
- Grouped requirements: `python scripts/run_batched.py <run> --size N --overview 800 [--split v4]`; whole document: `run_verdicts.py ... --whole`; top 20: `--candidates 20`.
- Decision layer with a feature preset (`all`, `no_wording`, `agnostic`): `python scripts/stack_verdicts.py <run> <target> --preset P` (cross-validated), `python scripts/apply_stacker.py <train run> <apply run> <target> --preset P`.
- The comparison tables of 10k: `python scripts/compare_variants.py data/reports/v4_comparison.md data/reports/v4_calls_and_context.md`. Cascade on dev and the checks of 10i were run with throw-away scripts that are not stored; the cascade rows of 10k are reproduced by `compare_variants.py`.
- Stored data: `data/retrieval/` (retrieval scores, rankings), `data/runs/` (free-form runs), `data/runs_verdict/<run>/` (records, `run_config.json` with the prompt, `verdict_metrics_dev.json`).
