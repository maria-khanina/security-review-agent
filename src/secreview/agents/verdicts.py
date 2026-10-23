"""The verdict a reviewer gives on one numbered policy requirement."""

from pydantic import BaseModel

from secreview.parsing.vocabulary import Verdict


class RequirementVerdict(BaseModel):
    requirement_id: str
    verdict: Verdict
    design_span: tuple[int, int] | None
