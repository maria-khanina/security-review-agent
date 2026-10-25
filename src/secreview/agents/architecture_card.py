"""A short card of the architecture of a service, extracted from its design."""

from pathlib import Path
from typing import Literal

import httpx
from pydantic import BaseModel, Field

from secreview.agents.case_materials import CaseMaterials
from secreview.datagen.settings import project_path
from secreview.llm.client import VllmChatClient
from secreview.parsing.findings import ReplyParseError, extract_json_object
from secreview.parsing.grounding import locate_quote
from secreview.review_settings import REVIEW_SETTINGS

ComponentKind = Literal[
    "api_gateway",
    "service",
    "database",
    "object_storage",
    "message_queue",
    "secret_store",
    "identity_provider",
    "client_app",
    "third_party",
    "ci_cd",
    "log_pipeline",
    "network",
]
DataClass = Literal["pii", "card_data", "credentials", "internal", "logs"]
Exposure = Literal["external", "internal", "admin", "unclear"]
Answer = Literal["yes", "no", "unclear"]

CARD_DIRECTORY = "data/cards"
MAX_CALLERS = len("abcdef")
MAX_DATA_CLASSES = len("abcde")
MAX_COMPONENTS = len("abcdefghijkl")
MAX_FLOWS = len("abcdefghijklmno")
CARD_SYSTEM_PROMPT = """You read a software design document and write a card of \
its architecture. Use only what the document says; when it does not say, use \
"unclear". Fill the fields:
- purpose: one sentence about what the service does.
- exposure: external when customers, merchants or partners outside the company \
call it; internal when only other company services call it; admin when only \
staff use it; unclear otherwise.
- callers: who calls the service or sends it data, as short phrases.
- serves_requests: yes when the service has an API that others call, no when it \
only consumes events or runs jobs, unclear otherwise.
- data_classes: the kinds of data the service handles.
- components: the parts of the service and its neighbours. Give the name as the \
document writes it, one kind from the list, and an evidence field with a short \
phrase copied character for character from the document.
- flows: arrows between components, with the kind of data that moves and an \
evidence field copied character for character from the document.
Answer with one JSON object only."""


class CardComponent(BaseModel):
    name: str
    kind: ComponentKind
    evidence: str


class CardFlow(BaseModel):
    source: str
    target: str
    data: str
    evidence: str


class ArchitectureCard(BaseModel):
    purpose: str
    exposure: Exposure
    callers: list[str] = Field(max_length=MAX_CALLERS)
    serves_requests: Answer
    data_classes: list[DataClass] = Field(max_length=MAX_DATA_CLASSES)
    components: list[CardComponent] = Field(max_length=MAX_COMPONENTS)
    flows: list[CardFlow] = Field(max_length=MAX_FLOWS)


def build_card_schema() -> dict[str, object]:
    """Return the JSON schema of the card."""
    schema: dict[str, object] = ArchitectureCard.model_json_schema()
    return schema


def card_path(name: str, case_id: str) -> Path:
    """Return the file of the card of one case."""
    return project_path(CARD_DIRECTORY) / name / f"{case_id}.json"


def has_card(name: str, case_id: str) -> bool:
    """Tell whether the card of a case was already extracted."""
    return card_path(name, case_id).exists()


def save_card(name: str, case_id: str, card: ArchitectureCard) -> None:
    """Write the card of a case."""
    path = card_path(name, case_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(card.model_dump_json(indent=1), encoding="utf-8")


def load_card(name: str, case_id: str) -> ArchitectureCard:
    """Read the card of a case."""
    text = card_path(name, case_id).read_text(encoding="utf-8")
    return ArchitectureCard.model_validate_json(text)


def is_grounded(design_text: str, evidence: str) -> bool:
    """Tell whether an evidence phrase occurs in the design text."""
    minimum = REVIEW_SETTINGS.grounding.min_quote_characters
    return locate_quote(design_text, evidence, minimum) is not None


def keep_grounded(card: ArchitectureCard, design_text: str) -> ArchitectureCard:
    """Drop the components and flows whose evidence is not in the document."""
    components: list[CardComponent] = [
        item for item in card.components if is_grounded(design_text, item.evidence)
    ]
    flows: list[CardFlow] = [
        item for item in card.flows if is_grounded(design_text, item.evidence)
    ]
    return card.model_copy(update={"components": components, "flows": flows})


def extract_card(
    client: VllmChatClient,
    materials: CaseMaterials,
) -> ArchitectureCard | None:
    """Ask the model for the card of a design, or nothing when the reply is bad."""
    text = materials.design_text[: REVIEW_SETTINGS.verdict.card_characters]
    reply = client.complete(CARD_SYSTEM_PROMPT, text, build_card_schema())
    try:
        card = ArchitectureCard.model_validate_json(extract_json_object(reply))
    except (ValueError, ReplyParseError):
        return None
    return keep_grounded(card, materials.design_text)


def render_card(card: ArchitectureCard) -> str:
    """Write a card as a few lines for the prompt of a verdict."""
    components = ", ".join(f"{item.name} ({item.kind})" for item in card.components)
    flows = "; ".join(
        f"{item.source} -> {item.target}: {item.data}" for item in card.flows
    )
    lines: list[str] = [
        "Service card, extracted from the whole design:",
        f"- purpose: {card.purpose}",
        f"- exposure: {card.exposure}; serves requests: {card.serves_requests}",
        f"- callers: {', '.join(card.callers) or 'not stated'}",
        f"- data: {', '.join(card.data_classes) or 'not stated'}",
        f"- components: {components or 'not stated'}",
        f"- flows: {flows or 'not stated'}",
    ]
    return "\n".join(lines)


def create_card(client: VllmChatClient, name: str, materials: CaseMaterials) -> bool:
    """Extract and store the card of a case; tell whether a card was made."""
    if has_card(name, materials.case_id):
        return False
    card = extract_card(client, materials)
    if card is None:
        return False
    save_card(name, materials.case_id, card)
    return True


def build_cards(name: str, materials_list: list[CaseMaterials]) -> int:
    """Extract the missing cards of the given cases; count the new ones."""
    with httpx.Client() as http_client:
        client = VllmChatClient(http_client)
        return sum(create_card(client, name, item) for item in materials_list)
