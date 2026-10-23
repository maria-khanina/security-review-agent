"""Retrieval questions drawn from the gold labels of a case."""

from pydantic import BaseModel

from secreview.agents.case_materials import CaseMaterials
from secreview.review_settings import REVIEW_SETTINGS

SATISFIED = "satisfied"
Span = tuple[int, int]


class RetrievalItem(BaseModel):
    case_id: str
    kind: str
    status: str
    query: str
    gold_spans: list[Span]


def to_spans(raw_spans: list[list[int]]) -> list[Span]:
    """Convert label spans into start and end pairs."""
    return [(span[0], span[1]) for span in raw_spans]


def build_items(
    materials: CaseMaterials,
    kind: str,
    status: str,
    policy_spans: list[list[int]],
    design_spans: list[list[int]],
) -> list[RetrievalItem]:
    """Create one item per policy sentence of a rule, sharing the design gold."""
    items: list[RetrievalItem] = []
    for start, end in to_spans(policy_spans):
        items.append(
            RetrievalItem(
                case_id=materials.case_id,
                kind=kind,
                status=status,
                query=materials.policy_text[start:end],
                gold_spans=to_spans(design_spans),
            )
        )
    return items


def build_flaw_items(materials: CaseMaterials) -> list[RetrievalItem]:
    """Create the items of the in-scope flaws that have a design location."""
    in_scope = REVIEW_SETTINGS.evaluation.in_scope_types
    items: list[RetrievalItem] = []
    for flaw in materials.labels.flaws:
        if flaw.type not in in_scope or not flaw.design_spans:
            continue
        policy_spans = flaw.policy_spans.get(flaw.rule_id or "", [])
        items.extend(
            build_items(
                materials,
                flaw.type,
                flaw.policy_status,
                policy_spans,
                flaw.design_spans,
            )
        )
    return items


def build_satisfied_items(materials: CaseMaterials) -> list[RetrievalItem]:
    """Create the items of the statements that satisfy a requirement."""
    items: list[RetrievalItem] = []
    for statement in materials.labels.satisfied:
        items.extend(
            build_items(
                materials,
                SATISFIED,
                "clear",
                statement.policy_spans,
                statement.design_spans,
            )
        )
    return items


def build_retrieval_items(materials: CaseMaterials) -> list[RetrievalItem]:
    """Return every retrieval question of a case, flaws first."""
    return build_flaw_items(materials) + build_satisfied_items(materials)
