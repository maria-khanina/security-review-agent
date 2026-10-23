"""Records of how each planted flaw and each finding fared in the matching."""

from pydantic import BaseModel


class GoldOutcome(BaseModel):
    case_id: str
    flaw_id: str
    flaw_type: str
    severity: str
    policy_status: str
    expected_action: str
    scorable: bool
    matched: bool
    evidence_correct: bool
    confidence: int
    predicted_type: str
    predicted_action: str
    predicted_severity: str

    @property
    def strict_matched(self) -> bool:
        """Tell whether both the design location and the evidence are right."""
        return self.matched and self.evidence_correct


class PredictionOutcome(BaseModel):
    case_id: str
    confidence: int
    matched_flaw_id: str | None
    strict_matched: bool


class CaseOutcome(BaseModel):
    case_id: str
    golds: list[GoldOutcome]
    predictions: list[PredictionOutcome]
    parse_failed: bool
    recovered: bool
    rejected_hallucinations: int
