"""Tests for the alternative wordings of satisfied rules."""

from string import ascii_letters

from secreview.datagen.catalog import load_rules
from secreview.datagen.markers import strip_markers
from secreview.datagen.phrasings import (
    choose_option,
    copies_statement,
    has_required_terms,
    is_standalone_sentence,
    is_weaker_wording,
    load_phrasings,
    load_strict_phrasings,
    rephrase_design,
)

RULE = "AUTH-04"
STRICT_RULE = "AUTH-06"
STRICT_VERSION = "v2"
LOOSE_VERSION = "v1"
VIOLATION_TEXT = "Staff may use a password alone."
TAIL = "- tail\n"
OPTIONS_PER_RULE = len("abcd")
CASE_IDS: list[str] = [f"c{letter}" for letter in ascii_letters]


def statement_of(rule_id: str) -> str:
    for rule in load_rules():
        if rule.id == rule_id:
            return rule.statement
    raise LookupError(rule_id)


def marked_design(rule_id: str) -> str:
    statement = statement_of(rule_id)
    return (
        "# Design\n\n"
        f"- ⟦S:{rule_id}|{statement}⟧\n"
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


def pick_wording(case_id: str, rule_id: str, version: str) -> str:
    varied = rephrase_design(case_id, version, marked_design(rule_id))
    assert rephrase_design(case_id, version, varied) == varied
    assert f"⟦F1|{VIOLATION_TEXT}⟧" in varied
    assert varied.endswith(TAIL)
    clean, spans = strip_markers(varied)
    start, end = spans[f"S:{rule_id}"][0]
    return clean[start:end]


def test_rephrasing_changes_only_satisfied_markers_and_is_stable() -> None:
    texts: set[str] = {
        pick_wording(case_id, RULE, LOOSE_VERSION) for case_id in CASE_IDS
    }
    allowed = set(load_phrasings()[RULE]) | {statement_of(RULE)}
    assert texts == allowed


def test_texts_that_are_not_copies_or_not_sentences_are_kept() -> None:
    own = "We use hardware keys for the admin console."
    marked = f"- ⟦S:{RULE}|{own}⟧\n"
    assert rephrase_design("c001", LOOSE_VERSION, marked) == marked
    fragment = f"- ⟦S:{RULE}|requires multi-factor authentication⟧\n"
    assert rephrase_design("c001", LOOSE_VERSION, fragment) == fragment
    assert not copies_statement(own, statement_of(RULE))


def test_a_version_with_extra_demands_gets_only_wordings_that_meet_them() -> None:
    strict: set[str] = set(load_strict_phrasings()[STRICT_RULE][STRICT_VERSION])
    texts: set[str] = {
        pick_wording(case_id, STRICT_RULE, STRICT_VERSION) for case_id in CASE_IDS
    }
    assert texts == strict
    assert statement_of(STRICT_RULE) not in texts


def test_a_general_wording_is_weaker_only_where_the_version_asks_more() -> None:
    general = statement_of(STRICT_RULE)
    assert is_weaker_wording(general, STRICT_RULE, STRICT_VERSION)
    assert not is_weaker_wording(general, STRICT_RULE, LOOSE_VERSION)
    for option in load_strict_phrasings()[STRICT_RULE][STRICT_VERSION]:
        assert not is_weaker_wording(option, STRICT_RULE, STRICT_VERSION)


def test_every_strict_wording_names_what_its_version_adds() -> None:
    for rule_id, versions in load_strict_phrasings().items():
        for version, options in versions.items():
            for option in options:
                assert has_required_terms(option, rule_id, version)


def test_a_free_statement_is_weak_unless_it_names_the_added_demand() -> None:
    plain = "Webhook payloads are signed and signatures verified."
    full = "Webhooks carry an HMAC signature and a timestamp that the receiver checks."
    assert is_weaker_wording(plain, "API-03", STRICT_VERSION)
    assert not is_weaker_wording(full, "API-03", STRICT_VERSION)
    assert not is_weaker_wording(plain, "API-03", LOOSE_VERSION)


def test_every_strict_wording_is_a_complete_sentence() -> None:
    for versions in load_strict_phrasings().values():
        for options in versions.values():
            assert len(options) == OPTIONS_PER_RULE
            assert all(is_standalone_sentence(option) for option in options)
