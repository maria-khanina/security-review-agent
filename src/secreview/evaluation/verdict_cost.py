"""Cost of a verdict run: model calls, prompt and generated tokens, seconds."""

import json
import os

from pydantic import BaseModel
from transformers import AutoTokenizer, PreTrainedTokenizerBase

from secreview.agents.case_materials import load_case_materials
from secreview.agents.policy_requirements import load_policy_analysis
from secreview.agents.verdict_contexts import extract_overview, list_fragments
from secreview.agents.verdict_prompts import (
    build_verdict_system_prompt,
    build_verdict_user_prompt,
)
from secreview.agents.verdict_review import RequirementRecord
from secreview.agents.verdict_store import load_verdict_record, verdict_run_directory
from secreview.agents.verdict_verifier import SYSTEM_PROMPT, build_verifier_user_prompt
from secreview.evaluation.verdict_run import list_run_case_ids, read_analysis_name
from secreview.retrieval.units import DesignUnit, split_units
from secreview.review_settings import REVIEW_SETTINGS

TOKENIZER_MODEL = "Qwen/Qwen3-Embedding-0.6B"
VERIFIER_ANSWER = '{"answer": "yes"}'


class CostSummary(BaseModel):
    documents: int
    calls: int
    prompt_tokens: int
    completion_tokens: int
    seconds: float
    estimated: bool


class CaseInputs(BaseModel):
    system: str
    overview: str
    texts: dict[str, str]
    units: list[DesignUnit]


class Tally(BaseModel):
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0


def load_tokenizer() -> PreTrainedTokenizerBase:
    """Load the tokenizer of the Qwen3 family from the local cache."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    return AutoTokenizer.from_pretrained(TOKENIZER_MODEL)


def read_choice(run_name: str) -> dict[str, object]:
    """Read the context and prompt choice stored with a run."""
    path = verdict_run_directory(run_name) / REVIEW_SETTINGS.verdict.run_config_file
    return dict(json.loads(path.read_text(encoding="utf-8"))["choice"])


def count_call(tokenizer: PreTrainedTokenizerBase, prompt: str, reply: str) -> Tally:
    """Count one call with the given prompt text and generated text."""
    return Tally(
        calls=1,
        prompt_tokens=len(tokenizer.encode(prompt)),
        completion_tokens=len(tokenizer.encode(reply)),
    )


def merge(first: Tally, second: Tally) -> Tally:
    """Add up two tallies."""
    return Tally(
        calls=first.calls + second.calls,
        prompt_tokens=first.prompt_tokens + second.prompt_tokens,
        completion_tokens=first.completion_tokens + second.completion_tokens,
    )


def estimate_record(
    tokenizer: PreTrainedTokenizerBase,
    system: str,
    overview: str,
    requirement: str,
    fragments: list[str],
    record: RequirementRecord,
    with_verifier: bool,
) -> Tally:
    """Count the verdict call of a record and, when asked, its verifier call."""
    user = build_verdict_user_prompt(requirement, fragments, overview)
    tally = count_call(tokenizer, system + user, record.raw_reply)
    if not with_verifier or record.verdict is None:
        return tally
    check = build_verifier_user_prompt(requirement, fragments, record)
    return merge(tally, count_call(tokenizer, SYSTEM_PROMPT + check, VERIFIER_ANSWER))


def load_case_inputs(
    run_name: str,
    case_id: str,
    choice: dict[str, object],
) -> CaseInputs:
    """Rebuild what the model was given for one stored case, except the fragments."""
    materials = load_case_materials(case_id)
    version = materials.labels.policy_version
    analysis = load_policy_analysis(read_analysis_name(run_name), version)
    characters = int(str(choice.get("overview_chars", 0)))
    overview = extract_overview(materials.design_text, characters)
    reasoned = bool(choice.get("reasoned", False))
    strict = bool(choice.get("strict", False))
    return CaseInputs(
        system=build_verdict_system_prompt(strict, bool(overview), reasoned),
        overview=overview,
        texts={item.id: item.quote for item in analysis.requirements},
        units=split_units(materials.design_text),
    )


def estimate_case(
    tokenizer: PreTrainedTokenizerBase,
    run_name: str,
    case_id: str,
    choice: dict[str, object],
    with_verifier: bool,
) -> Tally:
    """Rebuild the prompts of a stored case and count their tokens."""
    inputs = load_case_inputs(run_name, case_id, choice)
    total = Tally()
    for record in load_verdict_record(run_name, case_id).records:
        fragments = list_fragments(inputs.units, record.context_units)
        part = estimate_record(
            tokenizer,
            inputs.system,
            inputs.overview,
            inputs.texts[record.requirement_id],
            fragments,
            record,
            with_verifier,
        )
        total = merge(total, part)
    return total


def estimate_run_cost(run_name: str, with_verifier: bool) -> CostSummary:
    """Estimate the cost of a run that has no usage data from its stored prompts."""
    choice = read_choice(run_name)
    tokenizer = load_tokenizer()
    case_ids = list_run_case_ids(run_name)
    total = Tally()
    for case_id in case_ids:
        part = estimate_case(tokenizer, run_name, case_id, choice, with_verifier)
        total = merge(total, part)
    return CostSummary(
        documents=len(case_ids),
        calls=total.calls,
        prompt_tokens=total.prompt_tokens,
        completion_tokens=total.completion_tokens,
        seconds=0.0,
        estimated=True,
    )


def measured_run_cost(run_name: str) -> CostSummary:
    """Add up the usage that the client stored in the records of a run."""
    case_ids = list_run_case_ids(run_name)
    records: list[RequirementRecord] = []
    for case_id in case_ids:
        records.extend(load_verdict_record(run_name, case_id).records)
    return CostSummary(
        documents=len(case_ids),
        calls=sum(record.calls for record in records),
        prompt_tokens=sum(record.prompt_tokens for record in records),
        completion_tokens=sum(record.completion_tokens for record in records),
        seconds=sum(record.seconds for record in records),
        estimated=False,
    )
