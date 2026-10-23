"""Tests for the design chunking, the rankers and the retrieval metrics."""

from secreview.agents.case_materials import list_case_ids, load_case_materials
from secreview.retrieval.gold import RetrievalItem, build_retrieval_items
from secreview.retrieval.metrics import ItemScore, is_reachable, score_ranking
from secreview.retrieval.rankers import Bm25Ranker, HybridRanker, order_by_score
from secreview.retrieval.report import compute_differences, compute_intervals
from secreview.retrieval.units import build_chunks, split_units

DESIGN = (
    "# Title\n\nIntro line.\n\n## Access\n\n"
    "- Admins use MFA. Roles are per service.\n"
    "1. **Logs.** Failures are logged.\n"
    "- Last bullet\n\n## Data\n\n- Encrypted at rest.\n"
)
QUERY = "Administrators must use multi-factor authentication (MFA)."
LOGS_UNIT = len("abc")
ROLES_UNIT = len("ab")


class FixedRanker:
    def __init__(self, order: list[int]) -> None:
        self.order = order

    def rank(self, query: str, keys: list[str]) -> list[int]:
        return self.order


def test_units_are_sentences_with_exact_offsets_and_sections() -> None:
    units = split_units(DESIGN)
    texts: list[str] = [unit.text for unit in units]
    assert texts == [
        "Intro line.",
        "Admins use MFA.",
        "Roles are per service.",
        "**Logs.** Failures are logged.",
        "Last bullet",
        "Encrypted at rest.",
    ]
    for unit in units:
        assert DESIGN[unit.start:unit.end] == unit.text
    assert [unit.heading for unit in units][1] == "Access"
    assert units[0].section != units[1].section != units[-1].section


def test_windows_stay_inside_their_section() -> None:
    units = split_units(DESIGN)
    plain = build_chunks(units, 0, False)
    plain_keys: list[str] = [chunk.key for chunk in plain]
    assert plain_keys == [unit.text for unit in units]
    wide = build_chunks(units, 1, True)
    assert (wide[1].first, wide[1].last) == (1, 2)
    assert wide[1].key == "Access: Admins use MFA. Roles are per service."
    assert (wide[-1].first, wide[-1].last) == (len(units) - 1, len(units) - 1)
    assert (wide[0].first, wide[0].last) == (0, 0)


def test_order_by_score_breaks_ties_by_position() -> None:
    scores: list[float] = [1.0, 2.0, 2.0, 1.0]
    ranking = order_by_score(scores)
    assert ranking[:2] == [1, 2]
    assert ranking[2:] == [0, len(scores) - 1]


def test_bm25_prefers_the_chunk_that_shares_words_with_the_query() -> None:
    keys: list[str] = ["Backups run nightly.", "Administrators use MFA."]
    keys.append("Logs are kept.")
    assert Bm25Ranker().rank(QUERY, keys)[0] == 1


def test_hybrid_fuses_two_rankings_by_reciprocal_rank() -> None:
    first = FixedRanker([0, 1, 2])
    second = FixedRanker([2, 1, 0])
    ranking = HybridRanker(first, second).rank("query", ["a", "b", "c"])
    assert ranking == [0, 2, 1]


def other_units(count: int, excluded: int) -> list[int]:
    return [index for index in range(count) if index != excluded]


def make_item(gold_text: str) -> RetrievalItem:
    start = DESIGN.index(gold_text)
    span = (start, start + len(gold_text))
    return RetrievalItem(
        case_id="case",
        kind="violation",
        status="clear",
        query=QUERY,
        gold_spans=[span],
    )


def test_the_first_correct_chunk_gives_rank_one_and_minimal_context() -> None:
    units = split_units(DESIGN)
    chunks = build_chunks(units, 0, False)
    ranking: list[int] = [LOGS_UNIT] + other_units(len(units), LOGS_UNIT)
    score = score_ranking(make_item("Failures are logged."), units, chunks, ranking)
    assert score.values["hit_at_1"] == 1.0
    assert score.values["reciprocal_rank"] == 1.0
    assert score.values["full_characters"] == float(len(units[LOGS_UNIT].text))


def test_the_last_correct_chunk_needs_the_whole_document() -> None:
    units = split_units(DESIGN)
    chunks = build_chunks(units, 0, False)
    reverse = other_units(len(units), LOGS_UNIT) + [LOGS_UNIT]
    worst = score_ranking(make_item("Failures are logged."), units, chunks, reverse)
    assert worst.values["hit_at_1"] == 0.0
    assert worst.values["full_rank"] == float(len(units))
    assert worst.values["full_fraction"] == 1.0


def test_a_window_hits_through_its_neighbours_but_costs_more_context() -> None:
    units = split_units(DESIGN)
    item = make_item("Failures are logged.")
    plain = build_chunks(units, 0, False)
    wide = build_chunks(units, 1, False)
    neighbour_first = [ROLES_UNIT] + other_units(len(units), ROLES_UNIT)
    narrow_score = score_ranking(item, units, plain, neighbour_first)
    wide_score = score_ranking(item, units, wide, neighbour_first)
    assert narrow_score.values["hit_at_1"] == 0.0
    assert wide_score.values["hit_at_1"] == 1.0
    assert wide_score.values["full_characters"] > float(len(units[LOGS_UNIT].text))


def test_an_item_whose_gold_lies_outside_every_unit_is_unreachable() -> None:
    units = split_units(DESIGN)
    heading_item = make_item("## Access")
    assert not is_reachable(heading_item, units)
    assert is_reachable(make_item("Encrypted at rest."), units)


def test_every_labelled_dev_statement_can_be_reached_by_some_unit() -> None:
    total = 0
    unreachable = 0
    for case_id in list_case_ids("dev"):
        materials = load_case_materials(case_id)
        units = split_units(materials.design_text)
        for item in build_retrieval_items(materials):
            total += 1
            unreachable += int(not is_reachable(item, units))
    assert total > 0
    assert unreachable == 0


def score_copies() -> list[ItemScore]:
    units = split_units(DESIGN)
    chunks = build_chunks(units, 0, False)
    item = make_item("Failures are logged.")
    ranking: list[int] = list(range(len(units)))
    scores: list[ItemScore] = []
    for case_id in ("a", "b", "c", "d"):
        copy = item.model_copy(update={"case_id": case_id})
        scores.append(score_ranking(copy, units, chunks, ranking))
    return scores


def test_bootstrap_intervals_contain_the_estimate_and_paired_gaps_vanish() -> None:
    scores = score_copies()
    interval = compute_intervals(scores)["hit_at_5"]
    assert interval.low <= interval.estimate <= interval.high
    gap = compute_differences(scores, scores)["hit_at_5"]
    assert (gap.estimate, gap.low, gap.high) == (0.0, 0.0, 0.0)
