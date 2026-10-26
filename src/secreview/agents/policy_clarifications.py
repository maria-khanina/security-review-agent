"""The requirements of a policy that the policy owner has to make checkable."""

from pydantic import BaseModel

from secreview.agents.policy_requirements import PolicyAnalysis

CLEAR = "clear"


class Clarification(BaseModel):
    requirement_id: str
    quote: str
    wording: str


def list_clarifications(analysis: PolicyAnalysis) -> list[Clarification]:
    """List the requirements whose wording is not clear, in the policy order."""
    items: list[Clarification] = []
    for requirement in analysis.requirements:
        if requirement.wording != CLEAR:
            items.append(
                Clarification(
                    requirement_id=requirement.id,
                    quote=requirement.quote,
                    wording=requirement.wording,
                )
            )
    return items


def render_clarifications(version: str, items: list[Clarification]) -> str:
    """Write the clarifications of one policy version as a markdown section."""
    lines: list[str] = [f"## Policy {version}", ""]
    for item in items:
        lines.append(f"- {item.requirement_id} ({item.wording}): {item.quote}")
    return "\n".join([*lines, ""])
