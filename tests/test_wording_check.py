"""Tests for the preparation of requirement sentences before the wording call."""

from secreview.agents.wording_check import normalize_modals, split_clauses


def test_should_and_shall_are_read_as_must_in_any_case() -> None:
    assert normalize_modals("Logs SHOULD not hold secrets") == (
        "Logs must not hold secrets"
    )
    assert normalize_modals("Keys shall rotate and may expire") == (
        "Keys must rotate and may expire"
    )


def test_a_sentence_with_two_obligations_is_cut_in_two() -> None:
    sentence = "Backups must be encrypted, and restores must be tested."
    assert split_clauses(sentence) == [
        "Backups must be encrypted",
        "restores must be tested.",
    ]


def test_a_list_inside_one_obligation_is_not_cut() -> None:
    sentence = "Keys must be kept in KMS, rotated and never stored with data."
    assert split_clauses(sentence) == [sentence]
