"""The table that compares the variants of the pipeline on one set of designs."""

import shutil

import numpy as np
from pydantic import BaseModel

from secreview.agents.verdict_run_config import (
    load_run_config,
    with_analysis,
    write_run_config,
)
from secreview.agents.verdict_store import verdict_run_directory
from secreview.evaluation.variant_scores import (
    VariantData,
    VariantMetrics,
    interval_of,
    layer_probabilities,
    load_variant,
    raw_classes,
    raw_scores,
    score_variant,
    scores_of,
    shown_classes,
)
from secreview.evaluation.verdict_cost import measured_run_cost
from secreview.evaluation.verdict_stacking import (
    FEATURE_GROUPS,
    Labels,
    Matrix,
    preset_columns,
)
from secreview.review_settings import REVIEW_SETTINGS

PRESET_LABELS = {
    "no_wording": "layer without the wording",
    "agnostic": "layer independent of the policy",
    "all": "layer, all features (first wording)",
}
WORDED = "layer, all features (wording per requirement)"
PRIOR_GROUPS = ("overlap", "length", "topics")


class Cost(BaseModel):
    calls: float
    prompt_tokens: float
    seconds: float


class TableRow(BaseModel):
    label: str
    metrics: VariantMetrics
    recall_interval: tuple[float, float]
    precision_interval: tuple[float, float]
    cost: Cost


def cost_per_document(run: str) -> Cost:
    """Measure the calls, the prompt tokens and the seconds per document."""
    measured = measured_run_cost(run)
    documents = measured.documents
    return Cost(
        calls=measured.calls / documents,
        prompt_tokens=measured.prompt_tokens / documents,
        seconds=measured.seconds / documents,
    )


def scale_cost(cost: Cost, share: float) -> Cost:
    """Charge a share of a cost."""
    return Cost(
        calls=cost.calls * share,
        prompt_tokens=cost.prompt_tokens * share,
        seconds=cost.seconds * share,
    )


def make_row(
    label: str,
    data: VariantData,
    chosen: Labels,
    score: np.ndarray,
    cost: Cost,
) -> TableRow:
    """Score a variant and add the intervals of the recall and the precision."""
    index = np.arange(len(data.gold))
    return TableRow(
        label=label,
        metrics=score_variant(data, chosen, score, index),
        recall_interval=interval_of(data, chosen, score, "recall"),
        precision_interval=interval_of(data, chosen, score, "precision"),
        cost=cost,
    )


def with_wording_analysis(run: str) -> str:
    """Copy a run whose policy analysis is the one with the wording per requirement."""
    settings = REVIEW_SETTINGS.verdict
    name = settings.name_separator.join([run, settings.wording_suffix])
    target = verdict_run_directory(name)
    if not target.exists():
        shutil.copytree(verdict_run_directory(run), target)
        config = with_analysis(load_run_config(run), settings.wording_analysis_set)
        write_run_config(name, config)
    return name


def from_probabilities(probabilities: Matrix) -> tuple[Labels, np.ndarray]:
    """Turn class probabilities into chosen classes and scores of being shown."""
    return probabilities.argmax(axis=1).astype(np.int64), scores_of(probabilities)


def group_columns(groups: tuple[str, ...]) -> list[int]:
    """List the feature columns of the named groups."""
    columns: list[int] = []
    start = 0
    for name, width in FEATURE_GROUPS:
        if name in groups:
            columns.extend(range(start, start + width))
        start += width
    return columns


def layer_rows(
    label: str,
    dev: VariantData,
    test: VariantData,
    cost: Cost,
) -> list[TableRow]:
    """Rows of the layers that use the wording of the first policy analysis."""
    rows: list[TableRow] = []
    for preset, name in PRESET_LABELS.items():
        probabilities = layer_probabilities(dev, test, preset_columns(preset))
        chosen, score = from_probabilities(probabilities)
        rows.append(make_row(f"{label}: {name}", test, chosen, score, cost))
    return rows


def worded_row(label: str, dev_run: str, test_run: str, cost: Cost) -> TableRow:
    """Row of the layer that uses the wording judged for every requirement."""
    dev = load_variant(with_wording_analysis(dev_run))
    test = load_variant(with_wording_analysis(test_run))
    probabilities = layer_probabilities(dev, test, preset_columns("all"))
    chosen, score = from_probabilities(probabilities)
    return make_row(f"{label}: {WORDED}", test, chosen, score, cost)


def configuration_rows(label: str, dev_run: str, test_run: str) -> list[TableRow]:
    """Rows of one configuration: the raw answers and the layers on top of them."""
    dev, test = load_variant(dev_run), load_variant(test_run)
    cost = cost_per_document(test_run)
    raw = make_row(f"{label}: raw", test, raw_classes(test), raw_scores(test), cost)
    rows: list[TableRow] = [raw, *layer_rows(label, dev, test, cost)]
    rows.append(worded_row(label, dev_run, test_run, cost))
    return rows


def cascade_outcome(
    pairs: int,
    prior: Matrix,
    full: Matrix,
    share: float,
) -> tuple[Labels, np.ndarray]:
    """Choose classes and scores when the least sure share of pairs gets the model."""
    order = np.argsort(prior.max(axis=1))
    sent = np.zeros(pairs, dtype=bool)
    sent[order[: int(round(share * pairs))]] = True
    return from_probabilities(np.where(sent[:, None], full, prior))


def cascade_row(
    test: VariantData,
    prior: Matrix,
    full: Matrix,
    share: float,
    cost: Cost,
) -> TableRow:
    """Row of the cascade that sends the least sure share of pairs to the model."""
    chosen, score = cascade_outcome(len(test.gold), prior, full, share)
    label = f"cascade, {share:.0%} of the pairs sent to the model"
    return make_row(label, test, chosen, score, scale_cost(cost, share))


def cascade_rows(dev_run: str, test_run: str) -> list[TableRow]:
    """Rows of the layer without a model call and of the cascade."""
    dev, test = load_variant(dev_run), load_variant(test_run)
    prior = layer_probabilities(dev, test, group_columns(PRIOR_GROUPS))
    full = layer_probabilities(dev, test, preset_columns("no_wording"))
    cost = cost_per_document(test_run)
    chosen, score = from_probabilities(prior)
    label = "prior only, no model call"
    first = make_row(label, test, chosen, score, scale_cost(cost, 0.0))
    shares = REVIEW_SETTINGS.evaluation.cascade_shares
    later: list[TableRow] = [
        cascade_row(test, prior, full, share, cost) for share in shares
    ]
    return [first, *later]


def decision_row(label: str, run: str) -> TableRow:
    """A row for a run whose only signal is the chosen verdict."""
    data = load_variant(run)
    chosen = raw_classes(data)
    shown = np.isin(chosen, shown_classes()).astype(np.float64)
    row = make_row(label, data, chosen, shown, cost_per_document(run))
    unranked = row.metrics.model_copy(update={"recall_at_budgets": []})
    return row.model_copy(update={"metrics": unranked})


def format_row(row: TableRow) -> str:
    """Write a row as a line of a markdown table."""
    metrics, cost = row.metrics, row.cost
    low, high = row.recall_interval
    values: list[str] = [f"{value:.2f}" for value in metrics.recall_at_budgets]
    recalls = " / ".join(values) if values else "not ranked"
    return (
        f"| {row.label} | {metrics.recall:.2f} ({low:.2f} to {high:.2f}) | "
        f"{metrics.precision:.2f} | {metrics.false_alarms_per_document:.2f} | "
        f"{recalls} | {metrics.accuracy:.3f} | {metrics.tolerant_accuracy:.3f} | "
        f"{cost.calls:.1f} | {cost.prompt_tokens:,.0f} | {cost.seconds:.0f} |"
    )


def table_header() -> str:
    """Write the header of the markdown table."""
    names: list[str] = [
        "Variant",
        "Shown recall (95% interval)",
        "Shown precision",
        "False alarms per document",
        "Recall at 0.5 / 1 / 2 / 3 false alarms per document",
        "Accuracy",
        "Tolerant accuracy",
        "Calls",
        "Prompt tokens",
        "Seconds",
    ]
    separator = "|" + "---|" * len(names)
    return "\n".join(["| " + " | ".join(names) + " |", separator])


def render_table(rows: list[TableRow]) -> str:
    """Write the rows as a markdown table."""
    return "\n".join([table_header(), *[format_row(row) for row in rows]])
