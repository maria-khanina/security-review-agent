"""Tests for the alternative wordings of satisfied rules."""

from string import ascii_letters

from secreview.datagen.catalog import load_rules
from secreview.datagen.markers import strip_markers
from secreview.datagen.phrasings import (
    choose_option,
    copies_statement,
    is_standalone_sentence,
    load_phrasings,
    rephrase_design,
)

RULE = "AUTH-04"
VIOLATION_TEXT = "Staff may use a password alone."
TAIL = "- tail\n"
OPTIONS_PER_RULE = len("abcd")
CASE_IDS: list[str] = [f"c{letter}" for letter in ascii_letters]


def statement_of(rule_id: str) -> str:
    for rule in load_rules():
        if rule.id == rule_id:
            return rule.statement
    raise LookupError(rule_id)


def marked_design() -> str:
    statement = statement_of(RULE)
    return (
        "# Design\n\n"
        f"- ⟦S:{RULE}|{statement}⟧\n"
        f"- ⟦F1|{VIOLATION_TEXT}⟧\n"
        f"{TAIL}"
    )


def test_every_rule_has_distinct_complete_sentences() -> None:
    phrasings = load_phrasings()
    for rule in load_rules():
        options = phrasings[rule.id]
        assert len(options) == OPTIONS_PER_RULE
        assert len(set(options)) == len(options)
        for option in options:
            assert is_standalone_sentence(option)
            assert option != rule.statement


def test_the_choice_is_deterministic_and_spreads_over_all_options() -> None:
    first = choose_option("c001", RULE, OPTIONS_PER_RULE + 1)
    assert first == choose_option("c001", RULE, OPTIONS_PER_RULE + 1)
    seen: set[int] = set()
    for case_id in CASE_IDS:
        seen.add(choose_option(case_id, RULE, OPTIONS_PER_RULE + 1))
    assert seen == set(range(OPTIONS_PER_RULE + 1))


def pick_wording(case_id: str) -> str:
    varied = rephrase_design(case_id, marked_design())
    assert rephrase_design(case_id, varied) == varied
    assert f"⟦F1|{VIOLATION_TEXT}⟧" in varied
    assert varied.endswith(TAIL)
    clean, spans = strip_markers(varied)
    start, end = spans[f"S:{RULE}"][0]
    return clean[start:end]


def test_rephrasing_changes_only_satisfied_markers_and_is_stable() -> None:
    texts: set[str] = {pick_wording(case_id) for case_id in CASE_IDS}
    allowed = set(load_phrasings()[RULE]) | {statement_of(RULE)}
    assert texts == allowed


def test_texts_that_are_not_copies_or_not_sentences_are_kept() -> None:
    own = "We use hardware keys for the admin console."
    marked = f"- ⟦S:{RULE}|{own}⟧\n"
    assert rephrase_design("c001", marked) == marked
    fragment = f"- ⟦S:{RULE}|requires multi-factor authentication⟧\n"
    assert rephrase_design("c001", fragment) == fragment
    assert not copies_statement(own, statement_of(RULE))
