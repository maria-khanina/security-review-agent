"""Deterministic severity formula used to label planted flaws.

The gold severity of a flaw depends on the base impact of the violated rule,
how exposed the component is and how sensitive the data it holds is.
"""

from pydantic import BaseModel


class SeverityBin(BaseModel):
    upper_bound: float
    label: str


class Severity(BaseModel):
    exposure_multiplier: dict[str, float]
    data_multiplier: dict[str, float]
    compensating_control_multiplier: float
    ambiguity_step_down: int
    bins: list[SeverityBin]
    weights_for_risk_score: dict[str, int]

    def label_for(self, score: float) -> str:
        """Map a numeric severity score onto its named severity bin."""
        for severity_bin in self.bins:
            if score < severity_bin.upper_bound:
                return severity_bin.label
        return self.bins[-1].label

    def compute(
        self,
        base: int,
        exposure: str,
        data_class: str,
        has_compensating_control: bool,
        is_ambiguity: bool,
    ) -> str:
        """Compute the severity label of one flaw from its context."""
        score = base * self.exposure_multiplier[exposure]
        score *= self.data_multiplier[data_class]
        if has_compensating_control:
            score *= self.compensating_control_multiplier
        labels: list[str] = [severity_bin.label for severity_bin in self.bins]
        index = labels.index(self.label_for(score))
        if is_ambiguity:
            index = max(0, index - self.ambiguity_step_down)
        return labels[index]
