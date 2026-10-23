"""Numbered policy requirements: the ids are assigned by code, never by the model."""

import hashlib
from pathlib import Path

from pydantic import BaseModel

from secreview.datagen.settings import project_path
from secreview.parsing.grounding import locate_quote
from secreview.parsing.vocabulary import Topic, Wording
from secreview.review_settings import REVIEW_SETTINGS


class RequirementDraft(BaseModel):
    quote: str
    wording: Wording
    topics: list[Topic]


class PolicyRequirement(BaseModel):
    id: str
    quote: str
    span: tuple[int, int]
    wording: str
    topics: list[str]


class PolicyAnalysis(BaseModel):
    policy_version: str
    requirements: list[PolicyRequirement]


LocatedDraft = tuple[tuple[int, int], RequirementDraft]


def locate_drafts(
    policy_text: str,
    drafts: list[RequirementDraft],
) -> list[LocatedDraft]:
    """Keep the drafts whose quote is in the policy text, one per position."""
    minimum = REVIEW_SETTINGS.grounding.min_quote_characters
    located: dict[tuple[int, int], RequirementDraft] = {}
    for draft in drafts:
        span = locate_quote(policy_text, draft.quote, minimum)
        if span is not None and span not in located:
            located[span] = draft
    return sorted(located.items())


def number_requirements(
    policy_version: str,
    policy_text: str,
    located: list[LocatedDraft],
) -> PolicyAnalysis:
    """Number located drafts in text order, taking the quote from the policy."""
    prefix = REVIEW_SETTINGS.policy_analysis.requirement_prefix
    requirements: list[PolicyRequirement] = []
    for number, (span, draft) in enumerate(located, 1):
        requirements.append(
            PolicyRequirement(
                id=f"{prefix}{number}",
                quote=policy_text[span[0]:span[1]],
                span=span,
                wording=draft.wording,
                topics=list(draft.topics),
            )
        )
    return PolicyAnalysis(policy_version=policy_version, requirements=requirements)


def assign_requirements(
    policy_version: str,
    policy_text: str,
    drafts: list[RequirementDraft],
) -> PolicyAnalysis:
    """Verify the drafts against the policy text and number them in text order."""
    located = locate_drafts(policy_text, drafts)
    return number_requirements(policy_version, policy_text, located)


def render_tagged_policy(policy_text: str, analysis: PolicyAnalysis) -> str:
    """Insert the requirement ids before the requirement sentences."""
    pieces: list[str] = []
    position = 0
    for requirement in analysis.requirements:
        start, end = requirement.span
        pieces.append(policy_text[position:start])
        pieces.append(f"[{requirement.id}] {policy_text[start:end]}")
        position = end
    pieces.append(policy_text[position:])
    return "".join(pieces)


def find_requirement(
    analysis: PolicyAnalysis,
    requirement_id: str,
) -> PolicyRequirement | None:
    """Return the requirement with the given id, if the analysis has it."""
    for requirement in analysis.requirements:
        if requirement.id == requirement_id:
            return requirement
    return None


def list_requirement_ids(analysis: PolicyAnalysis) -> list[str]:
    """List the ids of all requirements of an analysis."""
    return [requirement.id for requirement in analysis.requirements]


def analysis_path(analysis_name: str, policy_version: str) -> Path:
    """Return the file of the stored analysis of one policy version."""
    directory = project_path(REVIEW_SETTINGS.policy_analysis.directory)
    return directory / analysis_name / f"policy_{policy_version}.json"


def save_policy_analysis(analysis_name: str, analysis: PolicyAnalysis) -> None:
    """Store the analysis of one policy version under a named analysis set."""
    path = analysis_path(analysis_name, analysis.policy_version)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(analysis.model_dump_json(indent=2), encoding="utf-8")


def load_policy_analysis(analysis_name: str, policy_version: str) -> PolicyAnalysis:
    """Read the stored analysis of one policy version."""
    path = analysis_path(analysis_name, policy_version)
    return PolicyAnalysis.model_validate_json(path.read_text(encoding="utf-8"))


def digest_analysis_set(analysis_name: str) -> str:
    """Return a digest of every stored file of an analysis set."""
    directory = analysis_path(analysis_name, "x").parent
    digest = hashlib.sha256()
    for path in sorted(directory.glob("*.json")):
        digest.update(path.read_bytes())
    return digest.hexdigest()
