"""Tests for case planning, flaw sampling, markers and processed cases."""

from collections import Counter
import json
import random

import pytest

from secreview.datagen.case_build import related_rules_of
from secreview.datagen.case_files import LABELS_FILE, processed_case_directory
from secreview.datagen.case_plan import plan_cases
from secreview.datagen.catalog import load_company, load_suppressed_rules
from secreview.datagen.flaw_sampling import sample_flaws
from secreview.datagen.labels import CaseLabels, FlawLabel
from secreview.datagen.markers import strip_markers
from secreview.datagen.models import Case, Flaw
from secreview.datagen.policies import PolicyVersion, load_policy_versions
from secreview.datagen.settings import PROJECT_ROOT, load_settings

HIGH_SEVERITIES = {"high", "critical"}
NESTED_MARKERS = "⟦F1|outer ⟦F2|inner⟧ text⟧"
MARKED_SAMPLE = "Intro. ⟦F1|We store PAN.⟧ Mid ⟦S:AUTH-01|OAuth2 only.⟧ End ⟦F1|Twice.⟧"
CLEAN_SAMPLE = "Intro. We store PAN. Mid OAuth2 only. End Twice."


@pytest.fixture(scope="module")
def sampled_cases() -> list[Case]:
    settings = load_settings()
    generator = random.Random(settings.seed + settings.flaw_seed_offset)
    cases: list[Case] = []
    for planned in plan_cases():
        sample_flaws(planned.case, generator, planned.defective)
        cases.append(planned.case)
    return cases


def finished_case_ids() -> list[str]:
    processed = PROJECT_ROOT / load_settings().paths.processed_directory
    return sorted(path.parent.name for path in processed.glob(f"*/{LABELS_FILE}"))


def load_labels(case_id: str) -> CaseLabels:
    """Read the gold labels of a finished case."""
    path = processed_case_directory(case_id) / LABELS_FILE
    return CaseLabels.model_validate(json.loads(path.read_text(encoding="utf-8")))


def assert_policy_spans_known(flaw: FlawLabel, policy: PolicyVersion) -> None:
    """Check that a flaw's policy spans come from the policy version."""
    for rule_id, spans in flaw.policy_spans.items():
        known: list[list[int]] = [list(span) for span in policy.rules[rule_id].spans]
        assert all(span in known for span in spans)


def test_plan_matches_company_configuration(sampled_cases: list[Case]) -> None:
    split = load_company().split
    clean: list[Case] = [case for case in sampled_cases if not case.flaws]
    assert len(sampled_cases) == split.dataset_size
    assert len(clean) == split.clean_cases
    for case in sampled_cases:
        is_holdout = case.documented_service in split.holdout_documented_services
        assert (case.split == "test") == is_holdout


def test_implementation_formats_follow_the_configured_share(
    sampled_cases: list[Case],
) -> None:
    split = load_company().split
    counts = Counter(case.implementation_format for case in sampled_cases)
    for implementation_format, share in split.implementation_share.items():
        assert counts[implementation_format] == round(split.dataset_size * share)


def test_flaws_do_not_collide(sampled_cases: list[Case]) -> None:
    maximum = load_settings().quality_gates.max_flaws_per_case
    for case in sampled_cases:
        rule_ids: list[str] = [
            flaw.rule_id for flaw in case.flaws if flaw.rule_id
        ]
        mutations: list[str] = [
            flaw.implementation_mutation
            for flaw in case.flaws
            if flaw.implementation_mutation
        ]
        assert len(case.flaws) <= maximum
        assert len(rule_ids) == len(set(rule_ids)), case.case_id
        assert len(mutations) == len(set(mutations)), case.case_id
        assert not set(rule_ids) & set(case.required_rules), case.case_id


def test_required_rules_exclude_rules_coupled_to_flaws(
    sampled_cases: list[Case],
) -> None:
    suppressed_by_rule = load_suppressed_rules()
    for case in sampled_cases:
        suppressed: set[str] = set()
        for flaw in case.flaws:
            for rule_id in related_rules_of(flaw):
                suppressed |= suppressed_by_rule.get(rule_id, set())
        assert not suppressed & set(case.required_rules), case.case_id


def coupled_to_flaws(labels: CaseLabels) -> set[str]:
    suppressed_by_rule = load_suppressed_rules()
    suppressed: set[str] = set()
    for flaw in labels.flaws:
        for rule_id in flaw.related_rules:
            suppressed |= suppressed_by_rule.get(rule_id, set())
    return suppressed


def test_finished_cases_state_no_rule_coupled_to_a_flaw() -> None:
    for planned in plan_cases():
        case_id = planned.case.case_id
        labels_path = processed_case_directory(case_id) / LABELS_FILE
        if not labels_path.exists():
            continue
        labels = CaseLabels.model_validate_json(labels_path.read_text("utf-8"))
        stated: set[str] = {item.rule_id for item in labels.satisfied}
        assert not coupled_to_flaws(labels) & stated, case_id


def load_finished_labels() -> list[CaseLabels]:
    finished: list[CaseLabels] = []
    for planned in plan_cases():
        path = processed_case_directory(planned.case.case_id) / LABELS_FILE
        if path.exists():
            finished.append(CaseLabels.model_validate_json(path.read_text("utf-8")))
    return finished


def policy_flaws(labels: list[CaseLabels]) -> list[tuple[str, FlawLabel]]:
    return [
        (case_labels.split, flaw)
        for case_labels in labels
        for flaw in case_labels.flaws
    ]


def statuses_in_split(labels: list[CaseLabels], split: str) -> list[str]:
    flaws = policy_flaws(labels)
    return [flaw.policy_status for flaw_split, flaw in flaws if flaw_split == split]


def test_finished_cases_flag_policy_review_by_status() -> None:
    for split, flaw in policy_flaws(load_finished_labels()):
        assert flaw.needs_policy_review == (flaw.policy_status != "clear"), split


def test_finished_cases_cover_every_policy_status_in_every_split() -> None:
    labels = load_finished_labels()
    for split in ("dev", "test"):
        statuses: set[str] = set(statuses_in_split(labels, split))
        assert statuses == {"clear", "vague", "conflicting"}, split


def test_finished_cases_reach_the_non_clear_flaw_share() -> None:
    minimum = load_settings().quality_gates.min_non_clear_flaw_share
    labels = load_finished_labels()
    for split in ("dev", "test"):
        statuses = statuses_in_split(labels, split)
        non_clear = sum(1 for status in statuses if status != "clear")
        assert non_clear / len(statuses) >= minimum, split


def test_manifest_matches_mutation_presence(sampled_cases: list[Case]) -> None:
    for case in sampled_cases:
        for flaw in case.flaws:
            has_mutation = flaw.implementation_mutation is not None
            assert (flaw.manifest == "design") == (not has_mutation)


def test_flaw_types_are_balanced_and_severe_flaws_are_common(
    sampled_cases: list[Case],
) -> None:
    gates = load_settings().quality_gates
    flaws: list[Flaw] = [flaw for case in sampled_cases for flaw in case.flaws]
    type_counts = Counter(flaw.type for flaw in flaws)
    severe: list[Flaw] = [
        flaw for flaw in flaws if flaw.severity in HIGH_SEVERITIES
    ]
    assert min(type_counts.values()) >= gates.min_flaws_per_type
    assert len(severe) >= gates.min_high_or_critical_flaws


def test_remediation_matches_flaw_type(sampled_cases: list[Case]) -> None:
    for case in sampled_cases:
        for flaw in case.flaws:
            if flaw.type == "ambiguity":
                assert flaw.remediation_options == []
                assert flaw.clarification_needed
            else:
                assert flaw.remediation_options, flaw.flaw_id
                assert flaw.clarification_needed is None


def test_clean_cases_still_have_required_statements(
    sampled_cases: list[Case],
) -> None:
    minimum = load_settings().quality_gates.min_required_rules_for_clean_case
    for case in sampled_cases:
        if not case.flaws:
            assert len(case.required_rules) >= minimum, case.case_id


def test_strip_markers_reports_exact_offsets() -> None:
    text, spans = strip_markers(MARKED_SAMPLE)
    assert text == CLEAN_SAMPLE
    first_texts: list[str] = [text[start:end] for start, end in spans["F1"]]
    assert first_texts == ["We store PAN.", "Twice."]
    start, end = spans["S:AUTH-01"][0]
    assert text[start:end] == "OAuth2 only."


def test_strip_markers_rejects_nested_markers() -> None:
    with pytest.raises(ValueError):
        strip_markers(NESTED_MARKERS)


@pytest.mark.parametrize("case_id", finished_case_ids())
def test_finished_case_flaw_labels_are_consistent(case_id: str) -> None:
    labels = load_labels(case_id)
    text = (processed_case_directory(case_id) / "design.md").read_text("utf-8")
    policy = load_policy_versions()[labels.policy_version]
    for flaw in labels.flaws:
        assert bool(flaw.design_spans) == (flaw.manifest != "impl")
        assert flaw.implementation_anchor or flaw.manifest == "design"
        for start, end in flaw.design_spans:
            assert 0 <= start < end <= len(text)
        assert_policy_spans_known(flaw, policy)


@pytest.mark.parametrize("case_id", finished_case_ids())
def test_finished_case_satisfied_labels_are_consistent(case_id: str) -> None:
    labels = load_labels(case_id)
    for satisfied in labels.satisfied:
        assert satisfied.design_spans
    assert labels.clean == (not labels.flaws)
    flaw_rules: set[str | None] = {flaw.rule_id for flaw in labels.flaws}
    satisfied_rules: set[str | None] = {item.rule_id for item in labels.satisfied}
    assert not flaw_rules & satisfied_rules
