"""Finalizes an authored case: validates it and writes its gold labels."""

from dataclasses import dataclass

from secreview.datagen.case_files import (
    DESIGN_FILE,
    LABELS_FILE,
    load_raw_case,
    marked_design_path,
    processed_case_directory,
    raw_case_directory,
    write_text,
)
from secreview.datagen.case_validation import validate_implementation, validate_markers
from secreview.datagen.implementation import implementation_file_name
from secreview.datagen.implementation_spans import compute_implementation_spans
from secreview.datagen.labels import (
    CaseLabels,
    FlawLabel,
    SatisfiedLabel,
    build_case_labels,
    build_flaw_label,
    build_satisfied_label,
)
from secreview.datagen.markers import MarkerSpans, strip_markers
from secreview.datagen.models import Case, Flaw
from secreview.datagen.policies import PolicyVersion, load_policy_versions

JSON_INDENT = 1


def related_rules_of(flaw: Flaw) -> list[str]:
    """List the policy rules a flaw is judged against."""
    if flaw.rule_id:
        return [flaw.rule_id]
    raise LookupError(flaw.flaw_id)


def build_all_labels(
    case: Case,
    implementation_file: str,
    marker_spans: MarkerSpans,
    policy: PolicyVersion,
) -> CaseLabels:
    """Build the labels of every flaw and satisfied rule of a case."""
    flaw_labels: list[FlawLabel] = []
    changed_lines = compute_implementation_spans(case)
    for flaw in case.flaws:
        flaw_labels.append(
            build_flaw_label(
                flaw,
                related_rules_of(flaw),
                marker_spans,
                policy,
                changed_lines.get(flaw.flaw_id, []),
            )
        )
    satisfied: list[SatisfiedLabel] = []
    for rule_id in case.required_rules:
        satisfied.append(build_satisfied_label(rule_id, marker_spans, policy))
    return build_case_labels(case, implementation_file, flaw_labels, satisfied)


def collect_problems(
    case: Case,
    marker_spans: MarkerSpans,
    implementation_text: str,
) -> list[str]:
    """Gather every consistency problem of an authored case."""
    problems = validate_markers(case, marker_spans)
    problems += validate_implementation(case, implementation_text)
    return problems


def write_processed_case(
    case: Case,
    design_text: str,
    implementation_text: str,
    labels: CaseLabels,
) -> None:
    """Write the final design, implementation and labels of a case."""
    directory = processed_case_directory(case.case_id)
    directory.mkdir(parents=True, exist_ok=True)
    write_text(directory / DESIGN_FILE, design_text)
    write_text(directory / labels.implementation_file, implementation_text)
    write_text(directory / LABELS_FILE, labels.model_dump_json(indent=JSON_INDENT))


@dataclass(frozen=True)
class AuthoredCase:
    case: Case
    design_text: str
    marker_spans: MarkerSpans
    implementation_file: str
    implementation_text: str


def load_authored_case(case_id: str) -> AuthoredCase:
    """Read the planned case, its annotated design and its artifact."""
    case = load_raw_case(case_id)
    marked_text = marked_design_path(case_id).read_text(encoding="utf-8")
    design_text, marker_spans = strip_markers(marked_text)
    file_name = implementation_file_name(case.implementation_format)
    path = raw_case_directory(case_id) / file_name
    implementation_text = path.read_text(encoding="utf-8")
    return AuthoredCase(case, design_text, marker_spans, file_name, implementation_text)


def finalize_case(case_id: str) -> CaseLabels:
    """Validate an authored case and publish it with its gold labels."""
    authored = load_authored_case(case_id)
    case = authored.case
    problems = collect_problems(
        case,
        authored.marker_spans,
        authored.implementation_text,
    )
    if problems:
        raise ValueError(f"{case_id}: " + "; ".join(problems))
    policy = load_policy_versions()[case.policy_version]
    labels = build_all_labels(
        case,
        authored.implementation_file,
        authored.marker_spans,
        policy,
    )
    write_processed_case(
        case,
        authored.design_text,
        authored.implementation_text,
        labels,
    )
    return labels
