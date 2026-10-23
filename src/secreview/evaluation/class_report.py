"""Per-class and ordinal agreement metrics for categorical finding attributes."""

from pydantic import BaseModel


class ClassScores(BaseModel):
    precision: float
    recall: float
    f1: float
    support: int


class ClassReport(BaseModel):
    accuracy: float
    macro_f1: float
    per_class: dict[str, ClassScores]
    confusion: dict[str, dict[str, int]]


class OrdinalReport(BaseModel):
    mean_absolute_error: float
    mean_signed_error: float
    within_one_accuracy: float
    exact_accuracy: float


def divide(numerator: float, denominator: float) -> float:
    """Divide, returning zero for an empty denominator."""
    return numerator / denominator if denominator else 0.0


def count_confusion(
    pairs: list[tuple[str, str]],
    classes: tuple[str, ...],
) -> dict[str, dict[str, int]]:
    """Count how often each gold class was predicted as each class."""
    confusion: dict[str, dict[str, int]] = {}
    for gold in classes:
        confusion[gold] = {predicted: 0 for predicted in classes}
    for gold, predicted in pairs:
        confusion[gold][predicted] += 1
    return confusion


def score_class(
    confusion: dict[str, dict[str, int]],
    label: str,
) -> ClassScores:
    """Compute precision, recall and F1 of one class from the confusion table."""
    true_positive = confusion[label][label]
    predicted = sum(row[label] for row in confusion.values())
    support = sum(confusion[label].values())
    precision = divide(true_positive, predicted)
    recall = divide(true_positive, support)
    f1 = divide(2 * precision * recall, precision + recall)
    return ClassScores(precision=precision, recall=recall, f1=f1, support=support)


def build_class_report(
    pairs: list[tuple[str, str]],
    classes: tuple[str, ...],
) -> ClassReport:
    """Summarize gold-versus-predicted class pairs of the matched findings."""
    confusion = count_confusion(pairs, classes)
    per_class: dict[str, ClassScores] = {}
    for label in classes:
        per_class[label] = score_class(confusion, label)
    correct = sum(confusion[label][label] for label in classes)
    macro_f1 = divide(sum(scores.f1 for scores in per_class.values()), len(classes))
    return ClassReport(
        accuracy=divide(correct, len(pairs)),
        macro_f1=macro_f1,
        per_class=per_class,
        confusion=confusion,
    )


def build_ordinal_report(
    pairs: list[tuple[str, str]],
    order: tuple[str, ...],
) -> OrdinalReport:
    """Measure how far predicted levels are from gold levels on an ordered scale."""
    levels: dict[str, int] = {label: rank for rank, label in enumerate(order)}
    signed: list[int] = [levels[predicted] - levels[gold] for gold, predicted in pairs]
    near = sum(1 for gap in signed if abs(gap) <= 1)
    return OrdinalReport(
        mean_absolute_error=divide(sum(abs(gap) for gap in signed), len(signed)),
        mean_signed_error=divide(sum(signed), len(signed)),
        within_one_accuracy=divide(near, len(signed)),
        exact_accuracy=divide(sum(1 for gap in signed if gap == 0), len(signed)),
    )
